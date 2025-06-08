from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """Request body for /chat endpoint."""

    session_id: int = Field(..., description="Target session ID", example=1)
    prompt: str = Field(..., description="User prompt", example="Hello")

class ChatResponse(BaseModel):
    """Response for /chat endpoint."""

    message: str = Field(..., description="LLM response text")
