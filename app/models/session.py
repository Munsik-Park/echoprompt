from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime

class SessionBase(SQLModel):
    name: str

class SessionCreate(SessionBase):
    pass

class SessionResponse(SessionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class SessionModel(SessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) 