from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class MessageNode(BaseModel):
    # Fields from MessageModel
    id: int
    content: str
    role: str
    created_at: datetime
    user_id: Optional[str] = None
    document_id: Optional[str] = None
    memory_type: Optional[str] = None

    # Children for the tree structure
    children: List['MessageNode'] = []

    # Pydantic v2 config for ORM mode
    model_config = {
        "from_attributes": True
    }

SessionMessageTreeResponse = List[MessageNode]

# Optional: If we need to create MessageNode from MessageModel that might have different field names or structures
# you might need a more custom factory method or validator, but for now, from_attributes should work if field names match.
