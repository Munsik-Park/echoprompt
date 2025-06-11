from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str
    session_id: int
    limit: int = 5

class QueryResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int
    status: str
    message: str
    metadata: Dict[str, Any]

class SemanticSearchRequest(BaseModel):
    """Request body for semantic search."""

    session_id: int = Field(..., description="Target session ID", example=1)
    query: str = Field(..., description="Query text", example="Hello")
    limit: int = Field(5, description="Number of results to return", example=5)

    class Config:
        from_attributes = True

class SemanticSearchResult(BaseModel):
    """Single search result with similarity score."""

    id: str = Field(..., description="Message ID")
    score: float = Field(..., description="Similarity score")
    payload: Dict[str, str] = Field(..., description="Message payload containing content and role")

    class Config:
        from_attributes = True

class SemanticSearchResponse(BaseModel):
    """Semantic search response."""

    results: List[SemanticSearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    status: str = Field("success", description="Response status")
    message: str = Field("", description="Response message")
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "session_id": None,
            "query": "",
            "limit": 5,
            "min_score": None,
            "max_score": None
        },
        description="Search metadata"
    )

    class Config:
        from_attributes = True

 