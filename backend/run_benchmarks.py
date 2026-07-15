import csv
import os
import random

from app.data.generator import generate_dataset

from app.algorithms.brute_force import BruteForceIndex
from app.algorithms.kd_tree import KDTreeIndex
from app.algorithms.hnsw import HNSWIndex
from app.algorithms.ivf import IVFIndex

from benchmarks.benchmark_runner import BenchmarkRunner

DATASET_SIZE = 1000
DIMENSIONS = 64

QUERY_COUNT = 100

K = 10

SEED = 42

def random_queries(dataset, count):

    random.seed(SEED)

    return random.sample(
        dataset,
        count
    )
def save_results_csv(results):
        """
        Save benchmark results to benchmarks/results/results.csv.

        Creates the output directory if it does not exist. Each BenchmarkResult
        becomes one row in the CSV.
        """
        output_dir = os.path.join(
            os.path.dirname(__file__),
            "benchmarks",
            "results",
        )
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "results.csv")

        with open(output_path, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                "Algorithm",
                "Dataset Size",
                "Dimensions",
                "Build Time",
                "Average Query Time",
                "Insert Time",
                "Delete Time",
                "Recall@K",
                "Memory Bytes",
                "Distance Computations",
                "Visited Nodes",
                "Vectors Scanned",
                "Clusters Scanned",
            ])
            for result in results:
                writer.writerow([
                    result.algorithm,
                    result.dataset_size,
                    result.dimensions,
                    result.build_time,
                    result.average_query_time,
                    result.insert_time,
                    result.delete_time,
                    result.recall_at_k,
                    result.memory_bytes,
                    result.distance_computations,
                    result.visited_nodes,
                    result.vectors_scanned,
                    result.clusters_scanned,
                ])
    
def main():

    print("main() started")

    print("=" * 60)

    print("Generating Dataset...")

    dataset = generate_dataset(

        size=DATASET_SIZE,

        dimensions=DIMENSIONS,

        seed=SEED

    )

    print(f"Dataset Size : {len(dataset)}")

    print(f"Dimensions  : {DIMENSIONS}")

    print()

    queries = random_queries(

        dataset,

        QUERY_COUNT

    )
        
    ground_truth = BruteForceIndex()

    for item in dataset:
        ground_truth.insert(item)

    algorithms = [

        ("Brute Force", BruteForceIndex()),

        ("KD Tree", KDTreeIndex()),

        ("HNSW", HNSWIndex()),

        ("IVF", IVFIndex()),

    ]

    results = []

    for name, index in algorithms:

        print(f"\nRunning {name} Benchmark...")

        runner = BenchmarkRunner(
            index,
            name,
        )

        result = runner.run(
            dataset=dataset,
            queries=queries,
            ground_truth_index=ground_truth,
            k=K,
        )

        results.append(result)

        print(result)
        
    save_results_csv(results)

    print("\nResults saved to benchmarks/results/results.csv")
        
        
    
    
if __name__ == "__main__":
    main()
    
