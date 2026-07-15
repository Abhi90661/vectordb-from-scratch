from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    algorithm: str

    dataset_size: int

    dimensions: int

    build_time: float

    average_query_time: float

    insert_time: float

    delete_time: float

    recall_at_k: float

    memory_bytes: int

    distance_computations: int

    visited_nodes: int

    vectors_scanned: int

    clusters_scanned: int