from sqlmodel import SQLModel, Field
from typing import Optional, List, Dict, Any # Added List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class MessageBase(SQLModel):
    """Common fields for a chat message."""

    content: str = Field(
        ...,
        description="Message content",
        sa_column_kwargs={"comment": "Hello, how are you?"},
    )
    role: str = Field(
        ...,
        description="Message sender role ('user' or 'assistant')",
        sa_column_kwargs={"comment": "user"},
    )

class MessageCreate(MessageBase):
    user_id: Optional[str] = None
    document_id: Optional[str] = None
    memory_type: Optional[str] = None

class MessageUpdate(SQLModel):
    """Schema for updating an existing message."""

    content: Optional[str] = Field(
        None,
        description="Updated message content",
        sa_column_kwargs={"comment": "Hi there!"},
    )
    role: Optional[str] = Field(
        None,
        description="Updated sender role",
        sa_column_kwargs={"comment": "assistant"},
    )

class MessageResponse(MessageBase):
    """Response model for a chat message."""

    id: int = Field(..., description="Message ID", sa_column_kwargs={"comment": "1"})
    session_id: int = Field(..., description="Associated session ID", sa_column_kwargs={"comment": "1"})
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(
        None,
        description="Last modification timestamp",
    )

class MessagePairResponse(BaseModel):
    """Response model for a pair of user and assistant messages."""

    message: MessageResponse = Field(..., description="Assistant message")
    user_message: MessageResponse = Field(..., description="User message")
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None

class MessageModel(MessageBase, table=True):
    """Database model for storing messages."""

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessionmodel.id")
    user_id: Optional[str] = Field(default=None)
    document_id: Optional[str] = Field(default=None)
    memory_type: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
 