from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import (
    CollectionModel,
    CollectionCreate,
    CollectionResponse,
    UserModel,
    UserResponse,
    CollectionUserLinkModel,
    CollectionUserLinkCreate,
    ErrorResponse,
    ErrorCode
)
from app.config import settings
from pydantic import BaseModel # Import BaseModel

router = APIRouter(
    prefix=f"{settings.API_PREFIX}/collections",
    tags=["Collections"]
)

# Helper function to get collection by name
def get_collection_by_name_or_404(collection_name: str, db: Session) -> CollectionModel:
    collection = db.query(CollectionModel).filter(CollectionModel.name == collection_name).first()
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error=ErrorCode.COLLECTION_NOT_FOUND,
                message=f"Collection with name '{collection_name}' not found."
            ).dict()
        )
    return collection

# Helper function to get user by ID or 404
def get_user_by_id_or_404(user_id: int, db: Session) -> UserModel:
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error=ErrorCode.USER_NOT_FOUND,
                message=f"User with ID {user_id} not found."
            ).dict()
        )
    return user


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(collection: CollectionCreate, db: Session = Depends(get_db)):
    try:
        db_collection = CollectionModel(**collection.dict())
        db.add(db_collection)
        db.commit()
        db.refresh(db_collection)
        return db_collection
    except IntegrityError: # Catches unique constraint violation for name
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=ErrorCode.COLLECTION_ALREADY_EXISTS,
                message=f"Collection with name '{collection.name}' already exists."
            ).dict()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.DATABASE_ERROR,
                message="Failed to create collection",
                details={"error": str(e)}
            ).dict()
        )

@router.get("", response_model=List[CollectionResponse])
async def get_collections(db: Session = Depends(get_db)):
    try:
        return db.query(CollectionModel).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.DATABASE_ERROR,
                message="Failed to retrieve collections",
                details={"error": str(e)}
            ).dict()
        )

@router.get("/{collection_name}", response_model=CollectionResponse)
async def get_collection(collection_name: str = Path(..., description="The name of the collection to retrieve"), db: Session = Depends(get_db)):
    return get_collection_by_name_or_404(collection_name, db)

class UserAddToCollectionRequest(BaseModel): # Changed from SQLModel to BaseModel
    user_id: int

@router.post("/{collection_name}/users", response_model=UserResponse)
async def add_user_to_collection(
    collection_name: str = Path(..., description="The name of the collection"),
    request_body: UserAddToCollectionRequest = Body(...),
    db: Session = Depends(get_db)
):
    collection = get_collection_by_name_or_404(collection_name, db)
    user = get_user_by_id_or_404(request_body.user_id, db)

    # Check if link already exists
    link = db.query(CollectionUserLinkModel).filter_by(collection_id=collection.id, user_id=user.id).first()
    if link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=ErrorCode.USER_ALREADY_IN_COLLECTION,
                message=f"User {user.id} is already in collection '{collection_name}'."
            ).dict()
        )

    try:
        new_link = CollectionUserLinkModel(collection_id=collection.id, user_id=user.id)
        db.add(new_link)
        db.commit()
        # Return the user that was added
        return user
    except IntegrityError: # Should be caught by the check above, but as a safeguard
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=ErrorCode.LINK_ALREADY_EXISTS, # Generic link error
                message=f"Link between user {user.id} and collection '{collection_name}' may already exist or other integrity issue."
            ).dict()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.DATABASE_ERROR,
                message="Failed to add user to collection",
                details={"error": str(e)}
            ).dict()
        )

@router.get("/{collection_name}/users", response_model=List[UserResponse])
async def get_users_in_collection(
    collection_name: str = Path(..., description="The name of the collection"),
    db: Session = Depends(get_db)
):
    collection = get_collection_by_name_or_404(collection_name, db)

    users = db.query(UserModel).join(CollectionUserLinkModel).filter(CollectionUserLinkModel.collection_id == collection.id).all()
    return users
