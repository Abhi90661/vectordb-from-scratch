from app.algorithms.brute_force import BruteForceIndex
from app.algorithms.kd_tree import KDTreeIndex
from app.algorithms.hnsw import HNSWIndex


class VectorDB:

    def __init__(self):

        self.indexes = {
            "bruteforce": BruteForceIndex(),
            "kdtree": KDTreeIndex(),
            "hnsw": HNSWIndex(),
        }

    def get(self, name):

        return self.indexes[name]