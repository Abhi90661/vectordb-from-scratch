import numpy as np

from app.core.metrics import (
    euclidean_distance,
    manhattan_distance,
    cosine_distance,
)


def test_euclidean_distance():
    a = np.array([0, 0])
    b = np.array([3, 4])

    assert euclidean_distance(a, b) == 5.0


def test_manhattan_distance():
    a = np.array([1, 2])
    b = np.array([4, 6])

    assert manhattan_distance(a, b) == 7


def test_cosine_distance_identical_vectors():
    a = np.array([1, 2, 3])
    b = np.array([1, 2, 3])

    assert abs(cosine_distance(a, b)) < 1e-6