from sqlmodel import SQLModel, Field
from typing import Optional

class CollectionUserLinkBase(SQLModel):
    collection_id: int = Field(..., foreign_key="collectionmodel.id", primary_key=True)
    user_id: int = Field(..., foreign_key="usermodel.id", primary_key=True)

class CollectionUserLinkCreate(CollectionUserLinkBase):
    pass

class CollectionUserLinkResponse(CollectionUserLinkBase):
    pass

class CollectionUserLinkModel(CollectionUserLinkBase, table=True):
    # No additional fields needed here as IDs are defined in Base
    pass
