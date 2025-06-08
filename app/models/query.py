from typing import List
from pydantic import BaseModel

class SemanticSearchRequest(BaseModel):
    session_id: int
    query: str
    limit: int = 5

class SemanticSearchResult(BaseModel):
    """Single search result with similarity score."""
    content: str
    score: float

class SemanticSearchResponse(BaseModel):
    """Semantic search response."""
    results: List[SemanticSearchResult]
