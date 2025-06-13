from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VectorPayload(BaseModel):
    user_id: str = Field(..., description="User identifier")
    session_id: int = Field(..., description="Associated session ID")
    message_id: int = Field(..., description="Associated message ID")
    role: str = Field(..., description="Message role ('user' or 'assistant')")
    content: str = Field(..., description="Original message content")
    summary: Optional[str] = Field(None, description="Optional summary of the message")
    token_count: int = Field(..., description="Token count of the content")
    timestamp: datetime = Field(..., description="Creation timestamp")
    memory_type: str = Field(..., description="Memory type such as 'short_term' or 'long_term'")
    importance: Optional[float] = Field(0.5, description="Relevance weighting")
    topic: Optional[str] = Field(None, description="Topic label")
    language: Optional[str] = Field("ko", description="Language code")
    source_type: Optional[str] = Field("chat", description="Source type")
    embedding_model: Optional[str] = Field("openai-ada-002", description="Embedding model name")
