from app.algorithms.brute_force import BruteForceIndex
from app.algorithms.kd_tree import KDTreeIndex
from app.data.generator import generate_dataset


def test_kdtree_matches_bruteforce():

    dataset = generate_dataset(
        size=100,
        dimensions=8,
        seed=42
    )

    brute = BruteForceIndex()
    kd = KDTreeIndex()

    for item in dataset:
        brute.insert(item)
        kd.insert(item)

    query = dataset[10].vector

    brute_results = brute.search(
        query=query,
        k=5,
        metric="euclidean"
    )

    kd_results = kd.search(
        query=query,
        k=5,
        metric="euclidean"
    )

    brute_ids = [item.id for item, _ in brute_results]
    kd_ids = [item.id for item, _ in kd_results]

    assert brute_ids == kd_ids