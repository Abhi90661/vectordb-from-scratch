import numpy as np

from app.algorithms.base import BaseIndex
from app.models.vector import VectorItem
from app.core.metrics import METRICS


class BruteForceIndex(BaseIndex):

    def __init__(self):
        self.items = []

    def insert(self, item: VectorItem):
        self.items.append(item)

    def delete(self, vector_id: str):
        self.items = [
            item for item in self.items
            if item.id != vector_id
        ]

    def size(self):
        return len(self.items)
    
    def search(self, query, k=5, metric="cosine"):

        distance_fn = METRICS[metric]

        results = []

        query = np.array(query)

        for item in self.items:

            vector = np.array(item.vector)

            distance = distance_fn(query, vector)

            results.append((item, distance))

        results.sort(key=lambda x: x[1])

        return results[:k]
    
    def update(self, item: VectorItem):
        for i, existing in enumerate(self.items):
            if existing.id == item.id:
                self.items[i] = item
                return True
        return False
    
    def upsert(self, item: VectorItem):

        for i, existing in enumerate(self.items):
            if existing.id == item.id:
                self.items[i] = item
                return

        self.items.append(item)