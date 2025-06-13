from sqlmodel import SQLModel, Field
from typing import Optional

class UserBase(SQLModel):
    user_identifier: str = Field(..., index=True, unique=True, description="Unique identifier for the user (e.g., email, username)")
    display_name: Optional[str] = Field(default=None, description="Display name for the user")

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int = Field(..., description="User ID")

class UserModel(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
