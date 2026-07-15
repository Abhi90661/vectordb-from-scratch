from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class VectorItem(BaseModel):
    id: str
    vector: List[float]
    metadata: Optional[Dict[str, Any]] = None