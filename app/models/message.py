from sqlmodel import SQLModel, Field
from typing import Optional, List, Literal # Import Literal
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
    document_id: Optional[str] = None
    memory_type: Literal["short_term", "long_term", "summary"] = Field("short_term", description="Type of memory for Qdrant") # Changed to Literal

class MessageUpdate(SQLModel):
    """Schema for updating an existing message."""
    document_id: Optional[str] = None
    memory_type: Optional[Literal["short_term", "long_term", "summary"]] = Field(None, description="Type of memory for Qdrant") # Changed to Literal

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

class MessageModel(MessageBase, table=True):
    """Database model for storing messages."""

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessionmodel.id")
    document_id: Optional[str] = Field(default=None, index=True) # New field
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

# Models for message tree structure (existing)
class MessageTreeNode(MessageResponse):
    """Represents a node in a message tree."""
    children: List['MessageTreeNode'] = []

# Update forward refs for MessageTreeNode - ensuring it's called after definition
MessageTreeNode.update_forward_refs()

# New models for document_id based grouping
class DocumentMessageGroup(BaseModel):
    """Represents a group of messages under a single document_id."""
    document_id: str
    messages: List[MessageTreeNode]

class SessionDocumentTreeResponse(BaseModel):
    """Response model for messages grouped by document_id."""
    __root__: List[DocumentMessageGroup]