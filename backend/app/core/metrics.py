import numpy as np


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    return np.linalg.norm(a - b)


def manhattan_distance(a: np.ndarray, b: np.ndarray) -> float:
    return np.sum(np.abs(a - b))


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 1.0

    cosine_similarity = np.dot(a, b) / denominator
    return 1 - cosine_similarity


METRICS = {
    "euclidean": euclidean_distance,
    "manhattan": manhattan_distance,
    "cosine": cosine_distance,
}