from app.algorithms.brute_force import BruteForceIndex
from app.models.vector import VectorItem


def test_insert_and_search():

    index = BruteForceIndex()

    index.insert(
        VectorItem(
            id="A",
            vector=[1.0, 1.0]
        )
    )

    index.insert(
        VectorItem(
            id="B",
            vector=[5.0, 5.0]
        )
    )

    results = index.search(
        query=[1.1, 1.1],
        k=1,
        metric="euclidean"
    )

    assert results[0][0].id == "A"