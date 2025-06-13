from pydantic import BaseModel, Field
from typing import Optional, Literal, List # Import List
from .retrieval import RetrievedChunk # Import RetrievedChunk

class ChatRequest(BaseModel):
    """Request body for /chat endpoint."""

    session_id: int = Field(..., description="Target session ID", example=1)
    prompt: str = Field(..., description="User prompt", example="Hello")
    document_id: Optional[str] = Field(None, description="Document ID associated with the prompt")
    user_identifier: Optional[str] = Field(None, description="User identifier for Qdrant filtering")
    memory_type: Literal["short_term", "long_term", "summary"] = Field("short_term", description="Type of memory to store")

class ChatResponse(BaseModel):
    """Response for /chat endpoint."""

    message: str = Field(..., description="LLM response text")
    retrieved_chunks: Optional[List[RetrievedChunk]] = Field(None, description="List of chunks retrieved and used for generating the response.")
