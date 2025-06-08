from typing import List
from pydantic import BaseModel, Field

class SemanticSearchRequest(BaseModel):
    """Request body for semantic search."""

    session_id: int = Field(..., description="Target session ID", example=1)
    query: str = Field(..., description="Query text", example="Hello")
    limit: int = Field(5, description="Number of results to return", example=5)

class SemanticSearchResult(BaseModel):
    """Single search result with similarity score."""

    content: str = Field(..., description="Retrieved message content")
    score: float = Field(..., description="Similarity score")

class SemanticSearchResponse(BaseModel):
    """Semantic search response."""

    results: List[SemanticSearchResult] = Field(..., description="Search results")

