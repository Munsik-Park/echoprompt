from pydantic import BaseModel
from typing import Optional, Literal # Import Literal
from datetime import datetime


class VectorPayload(BaseModel):
    user_id: str
    session_id: int
    message_id: int
    document_id: Optional[str] = None # New field
    role: str  # "user" or "assistant"
    content: str
    summary: Optional[str] = None # This field is for actual summary text, not a memory_type
    token_count: int
    timestamp: datetime
    memory_type: Literal["short_term", "long_term", "summary"] = "short_term"
    importance: Optional[float] = 0.5
    topic: Optional[str] = None
    language: Optional[str] = "ko"
    source_type: Optional[str] = "chat"
    embedding_model: Optional[str] = "openai-ada-002"
