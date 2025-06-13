from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class SessionBase(SQLModel):
    """Common fields for a chat session."""

    name: str = Field(
        ...,
        description="Name of the session",
        sa_column_kwargs={"comment": "My first session"},
    )
    user_id: Optional[int] = Field(default=None, foreign_key="usermodel.id", index=True) # New field

class SessionCreate(SessionBase):
    user_id: Optional[int] = None # New field, kept optional for now

class SessionUpdate(SQLModel):
    """Schema for updating an existing session."""

    name: Optional[str] = Field(
        None,
        description="Updated session name",
        sa_column_kwargs={"comment": "Updated session"},
    )

class SessionResponse(SessionBase):
    """Response model for session information."""

    id: int = Field(..., description="Session ID", sa_column_kwargs={"comment": "1"})
    user_id: Optional[int] = Field(default=None, description="Associated User ID") # New field
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(
        None,
        description="Last modification timestamp",
    )

class SessionModel(SessionBase, table=True):
    """Database model for storing sessions."""

    id: Optional[int] = Field(default=None, primary_key=True)
    # user_id is already in SessionBase, and SQLModel handles inheritance for table columns
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)