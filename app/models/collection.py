from sqlmodel import SQLModel, Field
from typing import Optional

class CollectionBase(SQLModel):
    name: str = Field(..., index=True, unique=True, description="Unique name for the collection")
    description: Optional[str] = Field(default=None, description="Description of the collection")

class CollectionCreate(CollectionBase):
    pass

class CollectionResponse(CollectionBase):
    id: int = Field(..., description="Collection ID")

class CollectionModel(CollectionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
