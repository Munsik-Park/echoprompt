from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List

class RetrievedChunk(BaseModel):
    id: Any = Field(..., description="Original ID of the retrieved chunk (e.g., Qdrant point ID).")
    content: Optional[str] = Field(None, description="Text content of the chunk.")
    score: float = Field(..., description="Retrieval score of the chunk.")
    document_id: Optional[str] = Field(None, description="Document ID associated with the chunk.")
    memory_type: Optional[str] = Field(None, description="Memory type of the chunk.")
    payload: Optional[Dict[str, Any]] = Field(None, description="Full Qdrant payload for additional details.")
