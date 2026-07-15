import heapq
import numpy as np
from dataclasses import dataclass
from typing import Optional

from app.algorithms.base import BaseIndex

from app.models.vector import VectorItem
from app.core.metrics import METRICS



@dataclass
class KDNode:
    item: VectorItem
    axis: int

    left: Optional["KDNode"] = None
    right: Optional["KDNode"] = None




class KDTreeIndex(BaseIndex):

    def __init__(self):
        self.root = None
        self.items = []
        # A KD-tree's shape depends on the full point set (median-split at
        # every level), so there's no cheap way to slot a single new point
        # into an already-built tree. Rather than rebuild on every insert
        # (which would make bulk loads -- VectorService.bulk_insert() calls
        # insert() once per item -- cost O(n^2 log n) instead of O(n log n)),
        # we lazily mark the tree stale and only rebuild the next time
        # search() actually needs it. This keeps single-insert correctness
        # (search always reflects everything inserted so far) without
        # paying a rebuild cost per item during bulk loads.
        self._dirty = False

    def insert(self, item):
        self.items.append(item)
        self._dirty = True

    def rebuild(self):
        self.root = self.build(self.items.copy())
        self._dirty = False

    def delete(self, vector_id):
        before = len(self.items)
        self.items = [item for item in self.items if item.id != vector_id]

        if len(self.items) == before:
            return False  # nothing with that id was found

        self._dirty = True
        return True

    def update(self, item: VectorItem) -> bool:
        """
        Replace an existing item's vector/metadata. Returns False (and does
        nothing) if `item.id` isn't currently stored, matching
        BruteForceIndex.update()'s contract. A changed vector can belong on
        a different side of a split, so this goes through the normal
        delete + insert path (which lazily marks the tree stale) rather
        than mutating a node's stored vector in place.
        """
        if not any(existing.id == item.id for existing in self.items):
            return False
        self.delete(item.id)
        self.insert(item)
        return True

    def upsert(self, item: VectorItem) -> None:
        """Update if `item.id` already exists, otherwise insert it fresh."""
        if any(existing.id == item.id for existing in self.items):
            self.delete(item.id)
        self.insert(item)

    from app.core.metrics import METRICS

    def search(self, query, k=5, metric="euclidean"):

        if self._dirty:
            self.rebuild()

        metric_fn =METRICS[metric]

        query = np.array(query)

        heap = []

        self._search(

            self.root,

            query,

            metric_fn,

            k,

            heap

        )

        results = [

            (item, -distance)

            for distance, item in heap

        ]

        results.sort(key=lambda x: x[1])

        return results
    
    def size(self):
        return len(self.items)
    
    def build(self, items, depth=0):

        if not items:
            return None

        axis = depth % len(items[0].vector)

        items.sort(key=lambda item: item.vector[axis])

        median = len(items) // 2

        node = KDNode(
            item=items[median],
            axis=axis
        )

        node.left = self.build(items[:median], depth + 1)

        node.right = self.build(items[median + 1:], depth + 1)

        return node
    

    def _search(self, node, query, metric_fn, k, heap):

        if node is None:
            return

        vector = np.array(node.item.vector)

        distance = metric_fn(query, vector)

        if len(heap) < k:
            heapq.heappush(heap, (-distance, node.item))
        else:
            if distance < -heap[0][0]:
                heapq.heapreplace(heap, (-distance, node.item))

        axis = node.axis

        if query[axis] < vector[axis]:
            near = node.left
            far = node.right
        else:
            near = node.right
            far = node.left

        self._search(near, query, metric_fn, k, heap)

        if len(heap) < k or abs(query[axis] - vector[axis]) < -heap[0][0]:
            self._search(far, query, metric_fn, k, heap)