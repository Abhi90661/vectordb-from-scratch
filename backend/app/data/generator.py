import numpy as np

from app.models.vector import VectorItem


def generate_dataset(size: int, dimensions: int, seed: int = 42):
    """
    Generate a synthetic dataset of random vectors.
    """

    np.random.seed(seed)

    dataset = []

    for i in range(size):

        vector = np.random.rand(dimensions).tolist()

        dataset.append(
            VectorItem(
                id=f"vec_{i}",
                vector=vector,
                metadata={}
            )
        )

    return dataset