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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ],
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