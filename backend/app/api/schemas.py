from pydantic import BaseModel
from typing import List, Dict, Any, Optional





class VectorCreate(BaseModel):
    id: str
    vector: List[float]
    metadata: dict = {}


class SearchRequest(BaseModel):

    query: List[float]

    k: int = 10
    metric: str = "cosine"

    filter: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    query: List[float]
    k: int = 10
    filter: Optional[Dict[str, Any]] = None

class DeleteRequest(BaseModel):
    id: str
    
    

class IndexRequest(BaseModel):
    index_type: str
    
class BulkVectorCreate(BaseModel):
    vectors: list[VectorCreate]
    
class BatchInsertRequest(BaseModel):
    vectors: List[VectorCreate]