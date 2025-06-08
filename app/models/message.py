from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class MessageBase(SQLModel):
    content: str
    role: str

class MessageCreate(MessageBase):
    pass

class MessageUpdate(SQLModel):
    """Message update model."""
    content: Optional[str] = None
    role: Optional[str] = None

class MessageResponse(MessageBase):
    id: int
    session_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class MessageModel(MessageBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessionmodel.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None 