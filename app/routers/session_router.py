from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body, Path, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.session import SessionModel, SessionCreate, SessionUpdate, SessionResponse
from app.models.message import MessageModel, MessageCreate, MessageUpdate, MessageResponse
from app.models.error import ErrorResponse, ErrorCode
from app.qdrant_client import get_qdrant_client, QdrantClientWrapper
from datetime import datetime

router = APIRouter(
    prefix="/api/v1/sessions",
    tags=["Sessions"]
)

@router.get("", response_model=List[SessionModel])
async def get_sessions(db: Session = Depends(get_db)):
    try:
        return db.query(SessionModel).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.DATABASE_ERROR,
                message="Failed to retrieve sessions",
                details={"error": str(e)}
            ).dict()
        )

@router.post("", response_model=SessionModel)
async def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    try:
        db_session = SessionModel(
            name=session.name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.SESSION_CREATE_FAILED,
                message="Failed to create session",
                details={"error": str(e)}
            ).dict()
        )

@router.get("/{session_id}", response_model=SessionModel)
async def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error=ErrorCode.SESSION_NOT_FOUND,
                message=f"Session with ID {session_id} not found"
            ).dict()
        )
    return session

@router.delete("/{session_id}")
async def delete_session(session_id: int, db: Session = Depends(get_db)):
    try:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error=ErrorCode.SESSION_NOT_FOUND,
                    message=f"Session with ID {session_id} not found"
                ).dict()
            )
        db.delete(session)
        db.commit()
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.SESSION_DELETE_FAILED,
                message="Failed to delete session",
                details={"error": str(e)}
            ).dict()
        )

@router.post(
    "/{session_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add message",
    description="Add a new message to the specified session.",
)
def create_message_endpoint(
    db: Session = Depends(get_db),
    session_id: int = Path(..., description="Session ID"),
    message: MessageCreate = Body(..., description="Message payload"),
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client)
):
    """Create a message and store its embedding."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 메시지 생성
    new_message = MessageModel(session_id=session_id, content=message.content, role=message.role)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # 전달받은 메시지 내용 로그 출력
    print(f"[DEBUG] message.content: {message.content}")
    
    # 임베딩 생성 및 저장
    if message.role == "user":
        embedding = qdrant_client.get_embedding(message.content)
        qdrant_client._ensure_collection(session_id)
        qdrant_client.store_embedding(
            message_id=new_message.id,
            session_id=session_id,
            content=message.content,
            embedding=embedding
        )

    return new_message

@router.get(
    "/{session_id}/messages",
    response_model=List[MessageResponse],
    summary="List session messages",
    description="Retrieve all messages within a session.",
)
def get_messages_endpoint(
    db: Session = Depends(get_db),
    session_id: int = Path(..., description="Session ID"),
):
    try:
        session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error=ErrorCode.SESSION_NOT_FOUND,
                    message=f"Session with ID {session_id} not found"
                ).dict()
            )
        
        messages = db.query(MessageModel).filter(MessageModel.session_id == session_id).all()
        return messages
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.DATABASE_ERROR,
                message="Failed to retrieve messages",
                details={"error": str(e)}
            ).dict()
        )

@router.delete(
    "/{session_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete message",
    description="Remove a message from a session and delete its embedding.",
)
def delete_message(
    session_id: int = Path(..., description="Session ID"),
    message_id: int = Path(..., description="Message ID"),
    db: Session = Depends(get_db),
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client)
):
    try:
        message = (
            db.query(MessageModel)
            .filter(MessageModel.id == message_id, MessageModel.session_id == session_id)
            .first()
        )
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error=ErrorCode.MESSAGE_NOT_FOUND,
                    message=f"Message with ID {message_id} not found in session {session_id}"
                ).dict()
            )

        qdrant_client.delete_embedding(message.id)
        db.delete(message)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.MESSAGE_DELETE_FAILED,
                message="Failed to delete message",
                details={"error": str(e)}
            ).dict()
        )

@router.put(
    "/{session_id}/messages/{message_id}",
    response_model=MessageResponse,
    summary="Update message",
    description="Update a message's content or role and regenerate its embedding.",
)
def update_message(
    session_id: int = Path(..., description="Session ID"),
    message_id: int = Path(..., description="Message ID"),
    message: MessageUpdate = Body(...),
    db: Session = Depends(get_db),
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client)
):
    """Update a message and regenerate its embedding."""
    message_obj = (
        db.query(MessageModel)
        .filter(MessageModel.id == message_id, MessageModel.session_id == session_id)
        .first()
    )
    if not message_obj:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.content is not None:
        message_obj.content = message.content
    if message.role is not None:
        message_obj.role = message.role

    db.commit()
    db.refresh(message_obj)

    # 임베딩 재생성
    if message.content is not None and message_obj.role == "user":
        embedding = qdrant_client.get_embedding(message.content)
        qdrant_client.store_embedding(
            message_id=message_id,
            session_id=session_id,
            content=message.content,
            embedding=embedding
        )

    return message_obj

@router.put(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Update session",
    description="Modify session information such as its name.",
)
def update_session(
    session_id: int = Path(..., description="Session ID"),
    session: SessionUpdate = Body(...),
    db: Session = Depends(get_db),
):
    try:
        session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error=ErrorCode.SESSION_NOT_FOUND,
                    message=f"Session with ID {session_id} not found"
                ).dict()
            )

        if session.name is not None:
            session_obj.name = session.name
        db.commit()
        db.refresh(session_obj)
        return session_obj
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.SESSION_UPDATE_FAILED,
                message="Failed to update session",
                details={"error": str(e)}
            ).dict()
        )
