from typing import List

from app.models.vector import VectorItem
from benchmarks.benchmark_result import BenchmarkResult
from benchmarks.benchmark_utils import (
    measure_time,
    estimate_memory,
    recall_at_k,
)


class BenchmarkRunner:

    def __init__(
        self,
        index,
        name: str,
    ):
        self.index = index
        self.name = name

    def run(
        self,
        dataset: List[VectorItem],
        queries: List[VectorItem],
        ground_truth_index,
        k: int = 10,
    ) -> BenchmarkResult:

        # ------------------------
        # Build Index
        # ------------------------

        _, build_time = measure_time(
            self._build,
            dataset,
        )

        # ------------------------
        # Query Benchmark
        # ------------------------

        total_query_time = 0.0

        total_recall = 0.0

        for query in queries:

            predicted, query_time = measure_time(
                self.index.search,
                query.vector,
                k,
            )

            expected = ground_truth_index.search(
                query.vector,
                k,
            )

            predicted_items = [
                item
                for item, _ in predicted
            ]

            expected_items = [
                item
                for item, _ in expected
            ]

            total_query_time += query_time

            total_recall += recall_at_k(
                predicted_items,
                expected_items,
            )

        average_query_time = (
            total_query_time / len(queries)
        )

        average_recall = (
            total_recall / len(queries)
        )

        return BenchmarkResult(
            algorithm=self.name,

            dataset_size=len(dataset),

            dimensions=len(dataset[0].vector),

            build_time=build_time,

            average_query_time=average_query_time,

            insert_time=0,

            delete_time=0,

            recall_at_k=average_recall,

            memory_bytes=estimate_memory(self.index),

            distance_computations=getattr(
                self.index,
                "distance_computations",
                0,
            ),

            visited_nodes=getattr(
                self.index,
                "visited_nodes",
                0,
            ),

            vectors_scanned=getattr(
                self.index,
                "vectors_scanned",
                0,
            ),

            clusters_scanned=getattr(
                self.index,
                "clusters_scanned",
                0,
            ),
        )

    def _build(
        self,
        dataset,
    ):
        for item in dataset:
            self.index.insert(item)