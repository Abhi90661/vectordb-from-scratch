from app.algorithms.hnsw import HNSWIndex
from app.data.generator import generate_dataset

dataset = generate_dataset(
    size=1000,
    dimensions=32,
    seed=42
)

index = HNSWIndex()

for item in dataset:
    index.insert(item)

query = dataset[50].vector

results = index.search(
    query=query,
    k=10
)

print("Results:", len(results))
print("Nearest ID:", results[0][0].id)
print("Distance:", results[0][1])