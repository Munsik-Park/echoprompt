from typing import List, Optional
from pydantic import BaseModel, Field

class MessageTreeNode(BaseModel):
    """Node representing a message and its children."""
    id: int = Field(..., description="Message ID")
    parent_id: Optional[int] = Field(None, description="Parent message ID")
    content: str = Field(..., description="Message content")
    role: str = Field(..., description="Sender role")
    children: List['MessageTreeNode'] = Field(default_factory=list, description="Child messages")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
