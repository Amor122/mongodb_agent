from pydantic import BaseModel
from typing import Dict, Any, Optional


class QueryRequest(BaseModel):
    collection: str
    filter: Optional[Dict[Any, Any]] = None
    projection: Optional[Dict[Any, Any]] = None
    sort: Optional[list] = None
    limit: Optional[int] = None
    skip: Optional[int] = None


class QueryResponse(BaseModel):
    data: list[Dict[Any, Any]]
    total: int
