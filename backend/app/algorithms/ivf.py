"""
IVF (Inverted File) index.

Educational, structurally-correct implementation inspired by FAISS's
IndexIVFFlat: vectors are partitioned into `n_clusters` Voronoi cells via
k-means, and a query is only compared against the vectors inside the
`nprobe` nearest cells -- trading exhaustive accuracy for speed by
searching a fraction of the dataset instead of all of it.

Why searching only the selected clusters works at all: k-means places
each centroid at the mean of a dense group of nearby vectors, so a
query's true nearest neighbors are, with high probability, sitting in
whichever cluster(s) the query itself is closest to. Skipping the other
clusters means skipping comparisons that were very unlikely to win
anyway -- that's the entire speed/accuracy trade IVF is built on.

What nprobe changes: `nprobe` is the number of nearest clusters searched
per query, not just one.
  - nprobe = 1  -> fastest, but a query sitting near a cluster boundary
    can miss true neighbors that landed just across that boundary in a
    different cell (a "boundary error"). This is the main source of
    recall loss in IVF.
  - nprobe = n_clusters -> equivalent to brute-force search (every vector
    gets compared), maximum recall, no speed benefit left.
  - Values in between let you trade recall for latency continuously:
    higher nprobe checks more clusters (higher recall, more distance
    computations) at the cost of scanning more vectors per query.

No external ANN or ML libraries are used. K-means (including k-means++
initialization) is implemented from scratch with NumPy only.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from app.algorithms.base import BaseIndex
from app.models.vector import VectorItem
from app.core.metrics import METRICS


@dataclass
class Cluster:
    centroid: np.ndarray
    item_ids: List[str] = field(default_factory=list)


class IVFIndex(BaseIndex):
    def __init__(
        self,
        n_clusters: int = 8,
        max_iterations: int = 100,
        tolerance: float = 1e-4,
        metric: str = "euclidean",
        nprobe: int = 1,
    ) -> None:
        if n_clusters < 1:
            raise ValueError("n_clusters must be an integer >= 1.")
        if max_iterations <= 0:
            raise ValueError("max_iterations must be a positive integer.")
        if tolerance < 0:
            raise ValueError("tolerance must be >= 0.")
        if metric not in METRICS:
            raise ValueError(f"Unknown metric '{metric}'. Options: {list(METRICS)}")
        if nprobe <= 0:
            raise ValueError("nprobe must be a positive integer.")

        self.n_clusters: int = n_clusters
        self.max_iterations: int = max_iterations
        self.tolerance: float = tolerance
        self.default_metric: str = metric
        self.nprobe: int = nprobe

        self.items: Dict[str, VectorItem] = {}
        self.numpy_vectors: Dict[str, np.ndarray] = {}

        self.clusters: Dict[int, Cluster] = {}
        self.item_cluster: Dict[str, int] = {}
        self._trained: bool = False

        self._pending_items: List[str] = []

        self.distance_computations: int = 0
        self.clusters_scanned: int = 0
        self.vectors_scanned: int = 0
        self._tracking: bool = False

    def size(self) -> int:
        return len(self.items)

    def insert(self, item: VectorItem) -> None:
        vector = np.asarray(item.vector, dtype=np.float64)
        self.items[item.id] = item
        self.numpy_vectors[item.id] = vector

        if not self._trained:
            self._pending_items.append(item.id)
            if len(self._pending_items) >= self.n_clusters:
                self._train()
            return

        distance_fn = METRICS[self.default_metric]
        cluster_id = self._nearest_cluster_id(vector, distance_fn)

        self.clusters[cluster_id].item_ids.append(item.id)
        self.item_cluster[item.id] = cluster_id

    def search(
        self,
        query: List[float],
        k: int,
        metric: str = "euclidean",
    ) -> List[Tuple[VectorItem, float]]:
        if k <= 0:
            raise ValueError("k must be a positive integer.")
        if metric not in METRICS:
            raise ValueError(f"Unknown metric '{metric}'. Options: {list(METRICS)}")

        if not self.items:
            return []

        distance_fn = METRICS[metric]
        query_vector = np.asarray(query, dtype=np.float64)

        self.distance_computations = 0
        self.clusters_scanned = 0
        self.vectors_scanned = 0
        self._tracking = True

        try:
            if self._trained:
                nprobe = self._effective_nprobe()
                selected_cluster_ids = self._nearest_cluster_ids(query_vector, distance_fn, nprobe)
                self.clusters_scanned = len(selected_cluster_ids)

                seen_ids: Set[str] = set()
                candidate_ids: List[str] = []
                for cluster_id in selected_cluster_ids:
                    for item_id in self.clusters[cluster_id].item_ids:
                        if item_id not in seen_ids:
                            seen_ids.add(item_id)
                            candidate_ids.append(item_id)
            else:
                candidate_ids = list(self.items.keys())
                self.clusters_scanned = 0

            scored: List[Tuple[str, float]] = []
            for item_id in candidate_ids:
                vector = self.numpy_vectors[item_id]
                dist = self._distance(query_vector, vector, distance_fn)
                scored.append((item_id, dist))
            self.vectors_scanned = len(candidate_ids)

            scored.sort(key=lambda pair: pair[1])
        finally:
            self._tracking = False

        top_k = scored[:k]
        return [(self.items[item_id], dist) for item_id, dist in top_k]

    def delete(self, id: str) -> None:
        item = self.items.pop(id, None)
        if item is None:
            return

        self.numpy_vectors.pop(id, None)

        if id in self._pending_items:
            self._pending_items.remove(id)

        cluster_id = self.item_cluster.pop(id, None)
        if cluster_id is not None:
            cluster = self.clusters.get(cluster_id)
            if cluster is not None and id in cluster.item_ids:
                cluster.item_ids.remove(id)

    def update(self, item: VectorItem) -> bool:
        """
        Replace an existing item's vector/metadata. Returns False (and does
        nothing) if `item.id` isn't currently stored, matching
        BruteForceIndex.update()'s contract.

        Implemented as delete-then-reinsert: a changed vector likely
        belongs in a different Voronoi cell than its old one, so the
        cluster assignment needs to be recomputed via the normal insert
        path rather than patched in place.
        """
        if item.id not in self.items:
            return False
        self.delete(item.id)
        self.insert(item)
        return True

    def upsert(self, item: VectorItem) -> None:
        """Update if `item.id` already exists, otherwise insert it fresh."""
        if item.id in self.items:
            self.delete(item.id)
        self.insert(item)

    def rebuild(self) -> None:
        if not self.items:
            self.clusters = {}
            self.item_cluster = {}
            self._pending_items = []
            self._trained = False
            return

        ids = list(self.items.keys())
        vectors = np.array([self.numpy_vectors[item_id] for item_id in ids])

        k = min(self.n_clusters, len(ids))

        centroids, assignments = self._run_kmeans(vectors, k)

        self.clusters = {
            cluster_idx: Cluster(centroid=centroids[cluster_idx], item_ids=[])
            for cluster_idx in range(k)
        }
        self.item_cluster = {}
        for item_id, cluster_idx in zip(ids, assignments):
            cluster_idx = int(cluster_idx)
            self.clusters[cluster_idx].item_ids.append(item_id)
            self.item_cluster[item_id] = cluster_idx

        self._pending_items = []
        self._trained = True

    def _distance(self, a: np.ndarray, b: np.ndarray, distance_fn) -> float:
        if self._tracking:
            self.distance_computations += 1
        return distance_fn(a, b)

    def _effective_nprobe(self) -> int:
        return min(self.nprobe, len(self.clusters))

    def _nearest_cluster_id(self, vector: np.ndarray, distance_fn) -> int:
        best_id: Optional[int] = None
        best_dist = float("inf")
        for cluster_id, cluster in self.clusters.items():
            dist = distance_fn(vector, cluster.centroid)
            if dist < best_dist:
                best_dist = dist
                best_id = cluster_id
        return best_id  # type: ignore[return-value]

    def _nearest_cluster_ids(
        self,
        vector: np.ndarray,
        distance_fn,
        nprobe: int,
    ) -> List[int]:
        scored_clusters: List[Tuple[int, float]] = [
            (cluster_id, self._distance(vector, cluster.centroid, distance_fn))
            for cluster_id, cluster in self.clusters.items()
        ]
        scored_clusters.sort(key=lambda pair: pair[1])
        return [cluster_id for cluster_id, _dist in scored_clusters[:nprobe]]

    def _train(self) -> None:
        ids = self._pending_items
        vectors = np.array([self.numpy_vectors[item_id] for item_id in ids])

        centroids, assignments = self._run_kmeans(vectors, self.n_clusters)

        self.clusters = {
            cluster_idx: Cluster(centroid=centroids[cluster_idx], item_ids=[])
            for cluster_idx in range(self.n_clusters)
        }
        for item_id, cluster_idx in zip(ids, assignments):
            cluster_idx = int(cluster_idx)
            self.clusters[cluster_idx].item_ids.append(item_id)
            self.item_cluster[item_id] = cluster_idx

        self._pending_items = []
        self._trained = True

    def _run_kmeans(self, vectors: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        centroids = self._initialize_centroids_kmeans_plus_plus(vectors, k)
        assignments = np.zeros(vectors.shape[0], dtype=int)

        for _iteration in range(self.max_iterations):
            diffs = vectors[:, None, :] - centroids[None, :, :]
            distances = np.linalg.norm(diffs, axis=2)
            new_assignments = np.argmin(distances, axis=1)

            new_centroids = np.zeros_like(centroids)
            for cluster_idx in range(k):
                members = vectors[new_assignments == cluster_idx]
                if len(members) > 0:
                    new_centroids[cluster_idx] = members.mean(axis=0)
                else:
                    new_centroids[cluster_idx] = vectors[random.randrange(vectors.shape[0])]

            shift = float(np.linalg.norm(new_centroids - centroids))
            centroids = new_centroids
            assignments = new_assignments

            if shift < self.tolerance:
                break

        return centroids, assignments

    def _initialize_centroids_kmeans_plus_plus(self, vectors: np.ndarray, k: int) -> np.ndarray:
        n_samples = vectors.shape[0]
        first_idx = random.randrange(n_samples)
        centroids = [vectors[first_idx]]

        while len(centroids) < k:
            centroid_matrix = np.array(centroids)
            diffs = vectors[:, None, :] - centroid_matrix[None, :, :]
            sq_distances_to_all = np.sum(diffs ** 2, axis=2)
            nearest_sq_distance = np.min(sq_distances_to_all, axis=1)

            total = nearest_sq_distance.sum()
            if total > 0:
                probabilities = nearest_sq_distance / total
                next_idx = np.random.choice(n_samples, p=probabilities)
            else:
                next_idx = random.randrange(n_samples)

            centroids.append(vectors[next_idx])

        return np.array(centroids)