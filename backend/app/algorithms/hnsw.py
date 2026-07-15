"""
HNSW (Hierarchical Navigable Small World) index.
 
Educational, structurally-correct implementation of the algorithm described in:
    Malkov, Y. A., & Yashunin, D. A. (2018).
    "Efficient and robust approximate nearest neighbor search using
    Hierarchical Navigable Small World graphs."
 
This implementation favors readability and correctness of the core algorithm
(layered graph, greedy descent, beam search, heuristic neighbor selection and
pruning) over the extra production optimizations used in libraries like
FAISS/hnswlib (e.g. no SIMD, no disk persistence, no incremental rebalancing).
"""
 
from __future__ import annotations
 
import math
import random
import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
 
import numpy as np
 
from app.algorithms.base import BaseIndex
from app.models.vector import VectorItem
from app.core.metrics import METRICS
 
 
# --------------------------------------------------------------------------- #
# Node
# --------------------------------------------------------------------------- #
 
@dataclass
class HNSWNode:
    """
    A single point stored in the HNSW graph.
 
    The original VectorItem is stored directly (id/vector/metadata are not
    duplicated as separate fields), so `search()` can return the exact same
    object that was inserted rather than reconstructing a new one.
 
    `neighbors` maps layer -> list of neighbor node ids connected to this
    node at that layer. A node exists on layers [0, level] inclusive, so
    `neighbors` only ever has keys in that range.
    """
    item: VectorItem
    level: int
    neighbors: Dict[int, List[str]] = field(default_factory=dict)
 
    def neighbors_at(self, layer: int) -> List[str]:
        """Return the neighbor id list at `layer`, creating it if absent."""
        if layer not in self.neighbors:
            self.neighbors[layer] = []
        return self.neighbors[layer]
 
 
# --------------------------------------------------------------------------- #
# Index
# --------------------------------------------------------------------------- #
 
class HNSWIndex(BaseIndex):
    """
    HNSW approximate nearest neighbor index.
 
    Parameters
    ----------
    M:
        Number of bidirectional links created per node at layers >= 1.
        Also used to derive M_max0, the (larger) cap used at layer 0, which
        the original paper sets to 2*M since layer 0 holds every node and
        benefits from a denser graph. Must be >= 2 (M=1 makes the level
        distribution formula, 1/ln(M), undefined).
    ef_construction:
        Size of the dynamic candidate list used while inserting. Larger
        values build a higher quality graph at the cost of slower inserts.
    ef_search:
        Default size of the dynamic candidate list used while searching at
        layer 0. Can be widened per-call if `k` exceeds it.
    metric:
        Default distance metric name, looked up in METRICS. `search()` may
        override this per call.
    extend_candidates:
        If True, SELECT-NEIGHBORS-HEURISTIC widens its candidate pool with
        each candidate's own neighbors before selecting. Matches the
        `extendCandidates` flag from Algorithm 4 in the paper.
    keep_pruned_connections:
        If True, SELECT-NEIGHBORS-HEURISTIC backfills the result with
        discarded (non-diverse) candidates if it didn't reach M selections.
        Matches the `keepPrunedConnections` flag from Algorithm 4.
    """
 
    def __init__(
        self,
        M: int = 8,
        ef_construction: int = 20,
        ef_search: int = 20,
        metric: str = "cosine",
        extend_candidates: bool = False,
        keep_pruned_connections: bool = True,
    ) -> None:
        if M < 2:
            raise ValueError("M must be an integer >= 2.")
        if ef_construction <= 0:
            raise ValueError("ef_construction must be a positive integer.")
        if ef_search <= 0:
            raise ValueError("ef_search must be a positive integer.")
        if metric not in METRICS:
            raise ValueError(f"Unknown metric '{metric}'. Options: {list(METRICS)}")
 
        self.M: int = M
        self.M_max0: int = M * 2  # Denser cap at layer 0, per the paper.
        self.ef_construction: int = ef_construction
        self.ef_search: int = ef_search
        self.default_metric: str = metric
 
        # Cache the default distance function once, instead of repeating a
        # METRICS[...] dictionary lookup on every insert.
        self._default_distance_fn = METRICS[metric]
 
        self.extend_candidates: bool = extend_candidates
        self.keep_pruned_connections: bool = keep_pruned_connections
 
        # m_L is the level-generation normalization factor. Using 1/ln(M)
        # gives the exponentially-decaying level distribution the paper
        # recommends, so on average only 1/M of nodes appear one layer up.
        self.m_L: float = 1.0 / math.log(M)
 
        self.nodes: Dict[str, HNSWNode] = {}
        self.entry_point: Optional[str] = None
        self.max_level: int = -1
 
        # Benchmark counters. Reset at the start of each search() call and
        # incremented only while a search is in flight (see `_tracking`),
        # so they reflect the cost of the most recent search only.
        self.distance_computations: int = 0
        self.visited_nodes: int = 0
        self.layers_traversed: int = 0
        self._tracking: bool = False
 
    # ------------------------------------------------------------------ #
    # Public API (BaseIndex contract)
    # ------------------------------------------------------------------ #
 
    def size(self) -> int:
        return len(self.nodes)
 
    def insert(self, item: VectorItem) -> None:
        vector = np.asarray(item.vector, dtype=np.float64)
        level = self._random_level()
 
        node = HNSWNode(item=item, level=level)
        self.nodes[item.id] = node
 
        # First node in an empty graph: it simply becomes the entry point.
        if self.entry_point is None:
            self.entry_point = item.id
            self.max_level = level
            return
 
        distance_fn = self._default_distance_fn
        current_nearest = self.entry_point
 
        # Phase 1: greedy descent from the top layer down to `level + 1`.
        # We only need the single closest node at each of these layers,
        # since they just serve as a "highway" to get near the insertion
        # point before we start actually connecting edges.
        for layer in range(self.max_level, level, -1):
            current_nearest = self._greedy_closest(vector, current_nearest, layer, distance_fn)
 
        # Phase 2: from min(max_level, level) down to 0, run a proper beam
        # search at each layer, select neighbors from the candidates found
        # via the diversity heuristic, and wire up bidirectional edges
        # (pruning neighbors that exceed the per-layer cap).
        top_layer_for_connections = min(self.max_level, level)
        for layer in range(top_layer_for_connections, -1, -1):
            candidates = self._search_layer(
                query=vector,
                entry_points=[current_nearest],
                ef=self.ef_construction,
                layer=layer,
                distance_fn=distance_fn,
            )
 
            layer_cap = self.M_max0 if layer == 0 else self.M
            selected = self._select_neighbors(vector, candidates, layer_cap, layer, distance_fn)
 
            # Connect the new node to its selected neighbors, and connect
            # each neighbor back to the new node (bidirectional), guarding
            # against duplicate edges in both directions.
            for neighbor_id, _dist in selected:
                new_node_edges = node.neighbors_at(layer)
                if neighbor_id not in new_node_edges:
                    new_node_edges.append(neighbor_id)
 
                neighbor_node = self.nodes[neighbor_id]
                neighbor_edges = neighbor_node.neighbors_at(layer)
                if item.id not in neighbor_edges:
                    neighbor_edges.append(item.id)
 
                self._prune_neighbors(neighbor_node, layer, layer_cap, distance_fn)
 
            if candidates:
                current_nearest = candidates[0][0]
 
        # If the new node reaches a higher level than anything seen so far,
        # it becomes the new entry point.
        if level > self.max_level:
            self.max_level = level
            self.entry_point = item.id
 
    def search(
        self,
        query: List[float],
        k: int,
        metric: str = "cosine",
    ) -> List[Tuple[VectorItem, float]]:
        if k <= 0:
            raise ValueError("k must be a positive integer.")
        if metric not in METRICS:
            raise ValueError(f"Unknown metric '{metric}'. Options: {list(METRICS)}")
 
        if self.entry_point is None or not self.nodes:
            return []
 
        distance_fn = METRICS[metric]
 
        # Reset benchmark counters for this search, and enable tracking so
        # internal helpers (_distance, _greedy_closest, _search_layer,
        # _select_neighbors) record their work below.
        self.distance_computations = 0
        self.visited_nodes = 0
        self.layers_traversed = 0
        self._tracking = True
 
        try:
            query_vector = np.asarray(query, dtype=np.float64)
            current_nearest = self.entry_point
 
            # Greedy descent from the top layer down to layer 1.
            for layer in range(self.max_level, 0, -1):
                self.layers_traversed += 1
                current_nearest = self._greedy_closest(query_vector, current_nearest, layer, distance_fn)
 
            # Beam search at layer 0, widening the candidate pool to at least k.
            self.layers_traversed += 1
            ef = max(self.ef_search, k)
            candidates = self._search_layer(
                query=query_vector,
                entry_points=[current_nearest],
                ef=ef,
                layer=0,
                distance_fn=distance_fn,
            )
        finally:
            self._tracking = False
 
        top_k = candidates[:k]
        results: List[Tuple[VectorItem, float]] = []
        for node_id, dist in top_k:
            # Return the original VectorItem instance directly -- no
            # reconstruction.
            results.append((self.nodes[node_id].item, dist))
        return results
 
    def delete(self, id: str) -> None:
        """
        Simple deletion: drop the node and strip references to it from
        every neighbor list that mentions it. No graph repair (e.g. no
        reconnection of the deleted node's former neighbors to each other)
        is performed, per the educational scope of this index.
        """
        node = self.nodes.pop(id, None)
        if node is None:
            return
 
        for layer, neighbor_ids in node.neighbors.items():
            for neighbor_id in neighbor_ids:
                neighbor_node = self.nodes.get(neighbor_id)
                if neighbor_node is None:
                    continue
                layer_neighbors = neighbor_node.neighbors_at(layer)
                if id in layer_neighbors:
                    layer_neighbors.remove(id)
 
        if self.entry_point == id:
            self._reassign_entry_point()

    def update(self, item: VectorItem) -> bool:
        """
        Replace an existing item's vector/metadata. Returns False (and does
        nothing) if `item.id` isn't currently in the graph, matching
        BruteForceIndex.update()'s contract.

        Implemented as delete-then-reinsert rather than patching the node
        in place: HNSW's edges are chosen based on the vector's position
        in space (SELECT-NEIGHBORS-HEURISTIC), so a changed vector needs a
        fresh set of graph connections anyway. This is a real re-insertion
        cost (same as insert()), which is a known HNSW limitation compared
        to indexes with cheaper in-place updates.
        """
        if item.id not in self.nodes:
            return False
        self.delete(item.id)
        self.insert(item)
        return True

    def upsert(self, item: VectorItem) -> None:
        """Update if `item.id` already exists, otherwise insert it fresh."""
        if item.id in self.nodes:
            self.delete(item.id)
        self.insert(item)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
 
    def _random_level(self) -> int:
        """
        Draw a random level using the exponential decay distribution from
        the paper: level = floor(-ln(u) * m_L), u ~ Uniform(0, 1).
 
        This makes higher layers exponentially sparser, which is what gives
        the graph its "highway to neighborhood" search behavior. `u` is
        re-drawn if it lands exactly on 0.0, since ln(0) is undefined.
        """
        u = random.random()
        while u == 0.0:
            u = random.random()
        return int(-math.log(u) * self.m_L)
 
    def _vector_of(self, node_id: str) -> np.ndarray:
        """Fetch a stored node's vector as a numpy array for distance math."""
        return np.asarray(self.nodes[node_id].item.vector, dtype=np.float64)
 
    def _distance(self, a: np.ndarray, b: np.ndarray, distance_fn) -> float:
        """Single choke point for distance calls, used to drive the
        `distance_computations` benchmark counter without scattering
        increments across every call site."""
        if self._tracking:
            self.distance_computations += 1
        return distance_fn(a, b)
 
    def _greedy_closest(
        self,
        query: np.ndarray,
        start_id: str,
        layer: int,
        distance_fn,
    ) -> str:
        """
        Single-best greedy search at `layer`: repeatedly move to whichever
        neighbor of the current node is closest to `query`, stopping when
        no neighbor improves on the current node. Used to descend through
        the upper "highway" layers, where we don't need a full candidate
        list, only the best entry point into the layer below.
        """
        current_id = start_id
        if self._tracking:
            self.visited_nodes += 1
        current_dist = self._distance(query, self._vector_of(current_id), distance_fn)
 
        improved = True
        while improved:
            improved = False
            current_node = self.nodes[current_id]
            for neighbor_id in current_node.neighbors_at(layer):
                neighbor_node = self.nodes.get(neighbor_id)
                if neighbor_node is None:
                    continue
                if self._tracking:
                    self.visited_nodes += 1
                dist = self._distance(query, self._vector_of(neighbor_id), distance_fn)
                if dist < current_dist:
                    current_dist = dist
                    current_id = neighbor_id
                    improved = True
 
        return current_id
 
    def _search_layer(
        self,
        query: np.ndarray,
        entry_points: List[str],
        ef: int,
        layer: int,
        distance_fn,
    ) -> List[Tuple[str, float]]:
        """
        Beam search at a single layer (Algorithm 2 in the paper).
 
        Maintains two heaps:
          - `candidates`: a min-heap of nodes still to explore, ordered by
            distance to the query (closest first).
          - `found`: a max-heap (via negated distance) of the best `ef`
            results seen so far, so we can cheaply check/evict the current
            worst result as better candidates are discovered.
 
        Returns up to `ef` (node_id, distance) pairs sorted by ascending
        distance (closest first).
        """
        visited: Set[str] = set(entry_points)
 
        candidates: List[Tuple[float, str]] = []
        found: List[Tuple[float, str]] = []  # stored as (-distance, id) for max-heap behavior
 
        for entry_id in entry_points:
            if self._tracking:
                self.visited_nodes += 1
            dist = self._distance(query, self._vector_of(entry_id), distance_fn)
            heapq.heappush(candidates, (dist, entry_id))
            heapq.heappush(found, (-dist, entry_id))
 
        while candidates:
            closest_dist, closest_id = heapq.heappop(candidates)
 
            # If the closest remaining candidate is already farther than our
            # current worst kept result, and we already have `ef` results,
            # nothing left in `candidates` can improve `found` further.
            worst_found_dist = -found[0][0]
            if closest_dist > worst_found_dist and len(found) >= ef:
                break
 
            closest_node = self.nodes.get(closest_id)
            if closest_node is None:
                continue
 
            for neighbor_id in closest_node.neighbors_at(layer):
                if neighbor_id in visited:
                    continue
                visited.add(neighbor_id)
                if self._tracking:
                    self.visited_nodes += 1
 
                neighbor_node = self.nodes.get(neighbor_id)
                if neighbor_node is None:
                    continue
 
                dist = self._distance(query, self._vector_of(neighbor_id), distance_fn)
                worst_found_dist = -found[0][0]
 
                if len(found) < ef or dist < worst_found_dist:
                    heapq.heappush(candidates, (dist, neighbor_id))
                    heapq.heappush(found, (-dist, neighbor_id))
                    if len(found) > ef:
                        heapq.heappop(found)
 
        results = [(node_id, -neg_dist) for neg_dist, node_id in found]
        results.sort(key=lambda pair: pair[1])
        return results
 
    def _select_neighbors(
        self,
        query: np.ndarray,
        candidates: List[Tuple[str, float]],
        M: int,
        layer: int,
        distance_fn,
    ) -> List[Tuple[str, float]]:
        """
        SELECT-NEIGHBORS-HEURISTIC (Algorithm 4, Malkov & Yashunin).
 
        Rather than simply keeping the M closest candidates -- which tends
        to cluster all of a node's connections toward one dense region of
        the graph -- this heuristic favors *diverse* neighbors: a candidate
        is only accepted into the result set R if it is closer to the query
        than it is to every neighbor already accepted into R. If a
        candidate is instead closer to an already-selected neighbor than to
        the query itself, that existing neighbor already "covers" the
        direction the candidate represents, so the candidate is discarded
        (or, if `keep_pruned_connections` is set and R is still under M,
        backfilled afterward). Spreading connections out directionally like
        this is what gives HNSW graphs good navigability.
        """
        # W: working candidate pool, keyed by id to avoid duplicate entries.
        working: Dict[str, float] = {node_id: dist for node_id, dist in candidates}
 
        if self.extend_candidates:
            # Optionally widen the candidate pool with each candidate's own
            # neighbors at this layer, in case a better-but-unseen candidate
            # is reachable through them.
            for node_id in list(working.keys()):
                node = self.nodes.get(node_id)
                if node is None:
                    continue
                for neighbor_id in node.neighbors_at(layer):
                    if neighbor_id not in working and neighbor_id in self.nodes:
                        dist = self._distance(query, self._vector_of(neighbor_id), distance_fn)
                        working[neighbor_id] = dist
 
        # Min-heap of (distance_to_query, id) so we can always "extract the
        # nearest remaining element", as the paper's pseudocode does.
        remaining: List[Tuple[float, str]] = [(dist, node_id) for node_id, dist in working.items()]
        heapq.heapify(remaining)
 
        selected: List[Tuple[str, float]] = []   # R
        discarded: List[Tuple[float, str]] = []  # W_d
 
        while remaining and len(selected) < M:
            dist_to_query, candidate_id = heapq.heappop(remaining)
            candidate_vector = self._vector_of(candidate_id)
 
            is_diverse = True
            for selected_id, _selected_dist in selected:
                dist_candidate_to_selected = self._distance(
                    candidate_vector, self._vector_of(selected_id), distance_fn
                )
                if dist_candidate_to_selected < dist_to_query:
                    is_diverse = False
                    break
 
            if is_diverse:
                selected.append((candidate_id, dist_to_query))
            else:
                discarded.append((dist_to_query, candidate_id))
 
        if self.keep_pruned_connections and len(selected) < M and discarded:
            discarded.sort(key=lambda pair: pair[0])
            for dist_to_query, candidate_id in discarded:
                if len(selected) >= M:
                    break
                selected.append((candidate_id, dist_to_query))
 
        selected.sort(key=lambda pair: pair[1])
        return selected
 
    def _prune_neighbors(
        self,
        node: HNSWNode,
        layer: int,
        cap: int,
        distance_fn,
    ) -> None:
        """
        If `node` has more than `cap` neighbors at `layer` after a new edge
        was added, keep only the `cap` closest ones (relative to `node`'s
        own vector) and drop the rest. This is the neighbor-pruning step
        that keeps the graph from growing unbounded degree over time.
        """
        neighbor_ids = node.neighbors_at(layer)
        if len(neighbor_ids) <= cap:
            return
 
        node_vector = self._vector_of(node.item.id)
        scored: List[Tuple[str, float]] = []
        for neighbor_id in neighbor_ids:
            neighbor_node = self.nodes.get(neighbor_id)
            if neighbor_node is None:
                continue
            dist = self._distance(node_vector, self._vector_of(neighbor_id), distance_fn)
            scored.append((neighbor_id, dist))
 
        scored.sort(key=lambda pair: pair[1])
        kept_ids = [neighbor_id for neighbor_id, _dist in scored[:cap]]
        dropped_ids = [neighbor_id for neighbor_id, _dist in scored[cap:]]
 
        node.neighbors[layer] = kept_ids
 
        # Keep the graph consistent: nodes that were dropped as neighbors
        # of `node` must also drop `node` from their own neighbor lists.
        for dropped_id in dropped_ids:
            dropped_node = self.nodes.get(dropped_id)
            if dropped_node is None:
                continue
            dropped_layer_neighbors = dropped_node.neighbors_at(layer)
            if node.item.id in dropped_layer_neighbors:
                dropped_layer_neighbors.remove(node.item.id)
 
    def _reassign_entry_point(self) -> None:
        """
        Called when the current entry point is deleted. Picks the
        remaining node with the highest level as the new entry point
        (falling back to None if the graph is now empty), and recomputes
        `max_level` accordingly.
        """
        if not self.nodes:
            self.entry_point = None
            self.max_level = -1
            return
 
        best_id = max(self.nodes, key=lambda node_id: self.nodes[node_id].level)
        self.entry_point = best_id
        self.max_level = self.nodes[best_id].level