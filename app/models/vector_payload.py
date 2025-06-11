from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VectorPayload(BaseModel):
    user_id: str
    session_id: int
    message_id: int
    role: str  # "user" or "assistant"
    content: str
    summary: Optional[str] = None
    token_count: int
    timestamp: datetime
    memory_type: str  # "short_term" or "long_term"
    importance: Optional[float] = 0.5
    topic: Optional[str] = None
    language: Optional[str] = "ko"
    source_type: Optional[str] = "chat"
    embedding_model: Optional[str] = "openai-ada-002"
