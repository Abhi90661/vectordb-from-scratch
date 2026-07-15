from fastapi import HTTPException
from fastapi import APIRouter







from app.api.schemas import (

    VectorCreate,

    BulkVectorCreate,

    SearchRequest,

    IndexRequest,
    BatchInsertRequest,

)

from app.services.vector_service import service

router = APIRouter()






@router.post("/vectors")
def insert_vector(vector: VectorCreate):
    service.insert(
        id=vector.id,
        vector=vector.vector,
        metadata=vector.metadata,
    )

    return {
        "message": "Vector inserted successfully"
    }
    
@router.post("/vectors/upsert")
def upsert_vector(request: VectorCreate):

    service.upsert(
        vector_id=request.id,
        vector=request.vector,
        metadata=request.metadata,
    )

    return {
        "message": "Vector upserted successfully"
    }
    
@router.post("/vectors/batch")
def batch_insert_vectors(request: BatchInsertRequest):

    inserted = service.batch_insert(request.vectors)

    return {
        "message": "Batch insert successful",
        "vectors_inserted": inserted,
    }
    
@router.post("/vectors/bulk")
def bulk_insert_vectors(request: BulkVectorCreate):

    service.bulk_insert(
        request.vectors
    )

    return {
        "message": "Vectors inserted successfully",
        "count": len(request.vectors),
    }


@router.post("/search")
def search_vectors(request: SearchRequest):

    results = service.search(
        query=request.query,
        k=request.k,
        filter=request.filter,
    )

    return [
        {
            "item": item.model_dump(),
            "distance": distance,
        }
        for item, distance in results
    ]
    


@router.delete("/vectors/{vector_id}")
def delete_vector(vector_id: str):

    deleted = service.delete(vector_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Vector not found",
        )

    return {
        "message": "Vector deleted successfully"
    }
    
@router.get("/stats")
def get_stats():

    vectors = service.get_all_vectors()

    dimensions = 0

    if vectors:
        dimensions = len(vectors[0].vector)

    return {
        "total_vectors": len(vectors),
        "index_type": service.index.__class__.__name__,
        "dimensions": dimensions,
        "memory_usage": "Coming Soon"
    }

@router.post("/index")
def change_index(request: IndexRequest):

    try:

        index_name = service.set_index(
            request.index_type
        )

        return {
            "message": "Index changed successfully",
            "index": index_name,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "VectorDB API",
    }
    
    
@router.get("/")
def root():
    return {
        "message": "Welcome to VectorDB API",
        "version": "1.0.0",
    }
    
@router.get("/vectors")
def get_vectors():
    return service.get_all_vectors()

@router.post("/save")
def save_database():

    count = service.save_database()

    return {
        "message": "Database saved successfully",
        "vectors_saved": count,
    }
    
@router.post("/load")
def load_database():
    count = service.load_database()

    return {
        "message": "Database loaded successfully",
        "vectors_loaded": count,
    }
    
    
@router.delete("/vectors")
def clear_vectors():
    service.clear()

    return {
        "message": "All vectors deleted successfully"
    }
    
    
@router.put("/vectors/{vector_id}")
def update_vector(vector_id: str, vector: VectorCreate):

    updated = service.update(
        id=vector_id,
        vector=vector.vector,
        metadata=vector.metadata,
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Vector not found",
        )

    return {
        "message": "Vector updated successfully"
    }
    
    
@router.get("/debug")
def debug():
    vectors = service.get_all_vectors()

    return {
        "index": service.index.__class__.__name__,
        "type": str(type(vectors)),
        "count": len(vectors),
    }