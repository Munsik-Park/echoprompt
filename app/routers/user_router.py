from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import (
    UserModel,
    UserCreate,
    UserResponse,
    SessionModel,
    SessionResponse,
    ErrorResponse,
    ErrorCode
)
from app.config import settings

router = APIRouter(
    prefix=f"{settings.API_PREFIX}/users",
    tags=["Users"]
)

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = UserModel(**user.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError: # Catches unique constraint violation for user_identifier
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error=ErrorCode.USER_ALREADY_EXISTS,
                message=f"User with identifier '{user.user_identifier}' already exists."
            ).dict()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.DATABASE_ERROR,
                message="Failed to create user",
                details={"error": str(e)}
            ).dict()
        )

@router.get("", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    try:
        return db.query(UserModel).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.DATABASE_ERROR,
                message="Failed to retrieve users",
                details={"error": str(e)}
            ).dict()
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int = Path(..., description="The ID of the user to retrieve"), db: Session = Depends(get_db)):
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

@router.get("/{user_id}/sessions", response_model=List[SessionResponse])
async def get_user_sessions(user_id: int = Path(..., description="The ID of the user whose sessions to retrieve"), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error=ErrorCode.USER_NOT_FOUND,
                message=f"User with ID {user_id} not found."
            ).dict()
        )

    sessions = db.query(SessionModel).filter(SessionModel.user_id == user_id).all()
    return sessions
