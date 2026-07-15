from app.algorithms.ivf import IVFIndex
from app.data.generator import generate_dataset


def test_ivf_insert_and_search():
    dataset = generate_dataset(
        size=100,
        dimensions=8,
        seed=42,
    )

    index = IVFIndex(
        n_clusters=8,
        nprobe=2,
    )

    for item in dataset:
        index.insert(item)

    query = dataset[20].vector

    results = index.search(
        query=query,
        k=5,
        metric="euclidean",
    )

    assert len(results) == 5

    nearest_item, distance = results[0]

    assert nearest_item.id == dataset[20].id

    assert distance >= 0