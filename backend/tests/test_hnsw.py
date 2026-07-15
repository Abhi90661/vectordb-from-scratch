from app.algorithms.hnsw import HNSWIndex
from app.data.generator import generate_dataset


def test_hnsw_insert_and_search():

    dataset = generate_dataset(
        size=100,
        dimensions=8,
        seed=42
    )

    hnsw = HNSWIndex()

    for item in dataset:
        hnsw.insert(item)

    query = dataset[20].vector

    results = hnsw.search(
        query=query,
        k=5,
        metric="euclidean"
    )

    assert len(results) == 5

    assert results[0][0].id == dataset[20].id