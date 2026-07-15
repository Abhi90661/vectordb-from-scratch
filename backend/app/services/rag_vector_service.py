from app.services.vector_service import VectorService

rag_service_db = VectorService(
    vector_file="storage/rag_vectors.json"
)