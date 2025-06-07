from typing import List
from pydantic import BaseModel

class SemanticSearchRequest(BaseModel):
    session_id: int
    query: str
    limit: int = 5

class SemanticSearchResponse(BaseModel):
    messages: List[str] 