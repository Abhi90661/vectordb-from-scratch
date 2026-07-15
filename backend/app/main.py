import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.upload import router as upload_router
from app.api.visualization import router as visualization_router
from app.api.pca import router as pca_router
from app.api.generate import router as generate_router
from app.api.rag_routes import router as rag_router


from app.api.benchmark import router as benchmark_router

app = FastAPI(title="VectorDB API")

# ALLOWED_ORIGINS lets the deployed frontend's real domain be added via an
# env var (e.g. on Render: ALLOWED_ORIGINS=https://your-app.vercel.app)
# without touching code. Falls back to local Vite dev ports so `npm run
# dev` keeps working untouched. Previously this list was hardcoded to
# localhost only, which would have silently blocked every request from a
# deployed frontend at the browser level (CORS failures don't show up as
# a clear backend error -- they just look like every request "does
# nothing").
default_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
]

extra_origins = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = default_origins + [
    origin.strip() for origin in extra_origins.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(upload_router)
app.include_router(visualization_router)
app.include_router(pca_router)
app.include_router(benchmark_router)
app.include_router(generate_router)
app.include_router(rag_router)