from fastapi import APIRouter
import random

from app.services.vector_service import service

router = APIRouter()

@router.post("/generate/{count}")
def generate_vectors(count: int):
    
    print("Generate endpoint called!")

    service.clear()

    for i in range(count):
        service.insert(
            id=f"vec_{i}",
            vector=[
    random.random()
    for _ in range(128)
],
            metadata={"class": random.randint(1,5)}
        )

    return {"vectors": service.size()}