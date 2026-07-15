import time

from fastapi import APIRouter
from app.services.vector_service import service
from app.algorithms.brute_force import BruteForceIndex
from app.algorithms.kd_tree import KDTreeIndex
from app.algorithms.ivf import IVFIndex
from app.algorithms.hnsw import HNSWIndex

router = APIRouter()

# Ordered so the results list comes back in a sensible, consistent order.
INDEX_CLASSES = {
    "bruteforce": BruteForceIndex,
    "kdtree": KDTreeIndex,
    "ivf": IVFIndex,
    "hnsw": HNSWIndex,
}


@router.get("/benchmark")
def benchmark():

    print("Starting benchmark")

    original_vectors = service.get_all_vectors().copy()

    print("Vectors loaded:", len(original_vectors))

    if not original_vectors:
        return {"error": "No vectors loaded"}

    # Use the first vector as the query
    query = original_vectors[0].vector

    results = []

    for algo, index_class in INDEX_CLASSES.items():

        print("================================")
        print("Testing:", algo)

        # Build each index directly and in isolation, inserting every real
        # vector exactly once, in memory only.
        #
        # The previous version routed each algorithm through a fresh
        # VectorService(), which (a) auto-loads whatever is currently on
        # disk at storage/vectors.json, then (b) called set_index(), which
        # re-inserts that loaded data into the new index, and then (c)
        # called bulk_insert(original_vectors) on top -- inserting the
        # same vectors a second time. Since BruteForceIndex/KDTreeIndex
        # store items in a plain list with no id-uniqueness check (unlike
        # IVFIndex/HNSWIndex, which are dict-keyed by id and self-dedupe),
        # and each iteration re-saved its inflated state back to the same
        # shared file for the next iteration to load, BruteForce ended up
        # benchmarked against ~2x the real data and KD-Tree against ~3x,
        # while IVF/HNSW were accidentally correct at 1x -- silently
        # biasing every comparison in IVF/HNSW's favor. Building indexes
        # fresh here, without touching VectorService or disk at all,
        # guarantees every algorithm is measured against the exact same
        # dataset, and also stops "Run Benchmark" from overwriting the
        # real persisted database as a side effect.
        index = index_class()

        for item in original_vectors:
            index.insert(item)

        if hasattr(index, "rebuild"):
            index.rebuild()

        print("Inserted:", index.size())

        print("Starting search")

        iterations = 100

        start = time.perf_counter()

        for _ in range(iterations):
            index.search(query, k=5)

        print("Finished search")

        end = time.perf_counter()

        elapsed = ((end - start) * 1000) / iterations

        print("Finished", algo)

        results.append({
            "algorithm": algo.upper(),
            "avg_time_ms": round(elapsed, 4),

            "distance_computations": getattr(index, "distance_computations", 0),

            "vectors_scanned": getattr(index, "vectors_scanned", 0),

            "clusters_scanned": getattr(index, "clusters_scanned", 0),

            "visited_nodes": getattr(index, "visited_nodes", 0),

            "layers_traversed": getattr(index, "layers_traversed", 0),
        })

    return results