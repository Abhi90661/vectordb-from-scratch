# vectordb-from-scratch

A vector database built from first principles in Python — no FAISS, no
hnswlib, no Pinecone, Weaviate, Milvus, or ChromaDB. Every index structure
and every nearest-neighbor algorithm is implemented from scratch using
NumPy, with a FastAPI backend, a React frontend, and a local
Retrieval-Augmented Generation (RAG) pipeline running entirely offline
against Ollama + Llama 3.2.

The goal isn't to compete with production vector databases — it's to
understand and demonstrate how they actually work under the hood: how
HNSW builds and searches a navigable small-world graph, how IVF partitions
a space into clusters, how a KD-Tree recursively splits dimensions, and
what a brute-force baseline costs by comparison.

## Why this exists

Most "vector database" portfolio projects wrap FAISS or ChromaDB and call
it done. This one doesn't use any of them — every algorithm below is
implemented and tested from scratch, so every design decision is
something I can actually explain, not just call.

## What's implemented

**Four nearest-neighbor index structures**, all built on raw NumPy:

| Index | Search | Build | Notes |
|---|---|---|---|
| Brute Force | O(n) | O(1) | Exact. The ground-truth baseline everything else is measured against. |
| KD-Tree | O(log n) average, degrades on high dimensions | O(n log n) | Exact. Real branch pruning (skips subtrees that can't contain a closer point). Lazily rebuilt: inserts/deletes mark the tree stale and it's rebuilt just before the next search, so a single insert doesn't cost a full rebuild but a search is never stale either. |
| IVF (Inverted File Index) | Sublinear, tunable via `nprobe` | O(n) to train clusters | Approximate. Clusters vectors with k-means++ initialization (not naive random seeding), then only searches the nearest clusters at query time. |
| HNSW (Hierarchical Navigable Small World) | O(log n) typical | O(n log n) | Approximate. Multi-layer navigable graph with the real SELECT-NEIGHBORS-HEURISTIC diversity-aware edge selection (Algorithm 4 from the original paper) — not just "keep the M closest candidates," which is a common shortcut that measurably degrades graph quality. |

**Three distance metrics**: cosine, Euclidean, Manhattan.

**Full CRUD** across all four index types: insert, delete, update, upsert,
batch insert, bulk insert (with a single save at the end rather than one
disk write per vector), save/load, clear.

**Metadata filtering** on search results (applied post-search — see
Design Decisions below for what that tradeoff actually means).

**Dynamic runtime index switching** — swap the active index type and all
existing vectors are migrated into the new structure automatically.

**Benchmarking** — build time, query time, and per-algorithm scan/traversal
counters (distance computations, vectors scanned, clusters scanned,
visited nodes, layers traversed), all measured against the *identical*
dataset for every algorithm so the comparison is actually fair (see
Design Decisions).

**PCA visualization** — project stored vectors to 2D via scikit-learn's
PCA + StandardScaler, rendered as a scatter plot colored by metadata
category.

**A fully local RAG pipeline**:

```
TXT upload → chunking → SentenceTransformer embeddings
    → inserted into the custom vector index
    → question asked → question embedded → similarity search
    → top-k chunks retrieved → passed to Ollama (Llama 3.2)
    → answer generated, grounded only in retrieved context
```

Multi-turn chat sessions persist to disk, including which source chunks
backed each answer, so a past conversation can be reopened with its
retrieval context intact.

## Architecture

```
React (Vite + Tailwind)
        │  Axios
        ▼
FastAPI routes  (app/api/)
        │
        ▼
VectorService   (app/services/) — CRUD orchestration, persistence,
        │                          index-agnostic dispatch
        ▼
Index layer     (app/algorithms/) — BruteForce | KDTree | IVF | HNSW
        │
        ▼
JSON persistence (storage/vectors.json, storage/chats.json)
```

RAG runs as a parallel path through the same vector index:

```
rag_service.py → embeds text via SentenceTransformer
              → stores/searches through the same VectorService
llm_service.py → sends retrieved context + question to Ollama (Llama 3.2)
chat_service.py → persists multi-turn conversation + sources to disk
```

## Tech stack

**Backend** — Python, FastAPI, NumPy, Pydantic, scikit-learn (PCA only),
SentenceTransformers, Ollama, Llama 3.2

**Frontend** — React, Vite, Tailwind CSS, Axios, Recharts

**Persistence** — JSON files (`storage/vectors.json`, `storage/chats.json`)

## Getting started

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

RAG needs a local Ollama instance with Llama 3.2 pulled:

```bash
ollama pull llama3.2
```

Then start the API:

```bash
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. `storage/` is created empty on a
fresh clone — the first vector insert or RAG upload will populate it.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

By default the frontend points at `http://127.0.0.1:8000`. To point it at
a deployed backend instead, set `VITE_API_URL` in the frontend's
environment.

### Seeding data

The dashboard starts empty. Either:
- Use the random vector generator (`POST /generate/{count}`) to populate
  the store with synthetic vectors for testing the indexes/benchmark, or
- Upload a CSV of real vectors via the Vector Explorer page, or
- Upload a `.txt` document via the RAG Demo page to populate it with real
  sentence-embedding chunks instead.

### Running tests

```bash
cd backend
pytest tests/ -q
```

## API reference

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/vectors` | Insert a vector |
| `PUT` | `/vectors/{id}` | Update a vector |
| `POST` | `/vectors/upsert` | Insert or update |
| `DELETE` | `/vectors/{id}` | Delete a vector |
| `DELETE` | `/vectors` | Clear the database |
| `GET` | `/vectors` | List all stored vectors |
| `POST` | `/vectors/batch` | Batch insert |
| `POST` | `/vectors/bulk` | Bulk insert (e.g. CSV import) |
| `POST` | `/search` | Top-k similarity search, with optional metadata filter |
| `POST` | `/index` | Switch the active index type |
| `GET` | `/stats` | Vector count, active index, dimensions, memory |
| `POST` | `/save` / `POST /load` | Manual persistence control |
| `GET` | `/benchmark` | Run all four algorithms against the current dataset |
| `GET` | `/pca` / `GET /visualize` | 2D PCA projection of stored vectors |
| `POST` | `/generate/{count}` | Generate synthetic random vectors |
| `POST` | `/upload` | CSV vector upload |
| `POST` | `/rag/upload` | Upload a `.txt` document for RAG |
| `POST` | `/rag/query` | Raw retrieval only, no generation |
| `POST` | `/rag/ask` | Full RAG: retrieve + generate an answer |
| `POST` | `/chat/new` | Start a new RAG chat session |
| `GET` | `/chat` / `GET /chat/{id}` | List chats / fetch one chat's history |

## Design decisions & known limitations

Written honestly, on purpose — these are the tradeoffs I'd want to be
asked about in an interview, not things I'd want someone else to find.

**Metadata filtering is post-search, not pre-search.** A query takes the
top-k nearest neighbors first, then filters by metadata — so a filtered
query can return fewer than k results even if more matches exist further
out in the index. This is a real, well-known tradeoff in production
vector databases too (pre-filtering restricts the candidate set before
the ANN search runs, which is more correct but usually more expensive to
implement well). I chose post-filtering for simplicity; a production
version would likely support both and let the caller choose.

**HNSW and IVF don't support cheap in-place updates.** Both `update()` and
`upsert()` are implemented as delete-then-reinsert rather than patching a
node in place. For HNSW this is because edges are chosen based on a
vector's position in space (via the diversity-aware neighbor heuristic),
so a changed vector needs a fresh set of graph connections regardless.
For IVF, a changed vector may belong to a different cluster entirely. This
is a real cost — repeated updates on these two indexes are as expensive
as a fresh insert.

**KD-Tree uses lazy rebuilding.** Because a KD-Tree's shape depends on the
entire point set (median-split at every level), there's no cheap way to
patch a single insert into an already-built tree. Rather than rebuild on
every insert (which would make bulk loads quadratic), inserts/deletes mark
the tree "dirty" and the next `search()` call rebuilds it if needed. This
keeps single inserts correct without punishing bulk imports.

**The benchmark measures every algorithm against an identical dataset.**
An earlier version of this endpoint round-tripped each algorithm through
shared on-disk state between iterations; because two of the four index
classes store items in a way that doesn't dedupe by id, that accidentally
gave different algorithms different amounts of data to search over,
biasing the comparison. The current implementation builds each index
fresh, in memory, from the same snapshot of vectors, so `avg_time_ms` and
the scan counters are a fair comparison.

**RAG chunking is naive fixed-size character slicing** (500 characters,
no overlap, no sentence-boundary awareness). It works, but it can and does
cut sentences mid-word. A production version would use sentence-aware or
overlapping chunking to avoid splitting context that belongs together.

**There's no collections/namespace concept.** All vectors — whether
manually inserted, CSV-uploaded, or RAG document chunks — live in a
single global store. A production version would separate these, the way
a real vector database separates data into collections or indexes per
use case.

**No concurrency control.** FastAPI can serve concurrent requests, but
there's no locking around index mutation, so a concurrent insert and
search (or two concurrent writes) aren't guaranteed to be safe. A
production version would need at minimum a reader-writer lock around
index state.

## Project structure

```
backend/
  app/
    algorithms/     # BruteForce, KDTree, IVF, HNSW — the actual index implementations
    api/            # FastAPI route handlers
    core/           # Distance metrics
    models/         # Pydantic schemas
    services/       # VectorService (CRUD orchestration), RAG/LLM/chat services
  benchmarks/       # Standalone benchmark runner + saved comparison graphs
  tests/            # pytest suite covering all four index types
frontend/
  src/
    api/            # Axios client
    components/     # Shared UI: Navbar, Sidebar, forms, tables
    pages/          # Dashboard, Vector Explorer, Search, Visualization, Benchmark, RAG Demo
```
