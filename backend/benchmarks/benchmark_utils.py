import sys
import time
from typing import List

from app.models.vector import VectorItem


def measure_time(func, *args, **kwargs):
    """
    Execute a function and measure its execution time.

    Returns:
        (result, elapsed_seconds)
    """

    start = time.perf_counter()

    result = func(*args, **kwargs)

    end = time.perf_counter()

    return result, end - start


def estimate_memory(index):
    """
    Very rough estimate of memory usage.

    This is not exact.
    It is sufficient for comparing algorithms.
    """

    return sys.getsizeof(index)


def recall_at_k(
    predicted: List[VectorItem],
    expected: List[VectorItem],
):
    """
    Compute Recall@K.

    Recall =
    (# correct results) / (# expected results)
    """

    if len(expected) == 0:
        return 0.0

    predicted_ids = {
        item.id
        for item in predicted
    }

    expected_ids = {
        item.id
        for item in expected
    }

    correct = len(
        predicted_ids.intersection(
            expected_ids
        )
    )

    return correct / len(expected_ids)