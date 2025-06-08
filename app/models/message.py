from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class MessageBase(SQLModel):
    """Common fields for a chat message."""

    content: str = Field(
        ...,
        description="Message content",
        example="Hello, how are you?",
    )
    role: str = Field(
        ...,
        description="Message sender role ('user' or 'assistant')",
        example="user",
    )

class MessageCreate(MessageBase):
    pass

class MessageUpdate(SQLModel):
    """Schema for updating an existing message."""

    content: Optional[str] = Field(
        None,
        description="Updated message content",
        example="Hi there!",
    )
    role: Optional[str] = Field(
        None,
        description="Updated sender role",
        example="assistant",
    )

class MessageResponse(MessageBase):
    """Response model for a chat message."""

    id: int = Field(..., description="Message ID", example=1)
    session_id: int = Field(..., description="Associated session ID", example=1)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(
        None,
        description="Last modification timestamp",
    )

class MessageModel(MessageBase, table=True):
    """Database model for storing messages."""

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessionmodel.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
