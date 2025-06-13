from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class MessageTreeNode(BaseModel):
    """Node representing a message in a conversation tree."""

    id: int = Field(..., description="Message ID")
    content: str = Field(..., description="Message content")
    role: str = Field(..., description="Sender role")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    children: List["MessageTreeNode"] = Field(default_factory=list, description="Child messages")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


MessageTreeNode.model_rebuild()
