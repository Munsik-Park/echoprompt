from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body, Path, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import (
    SessionModel,
    SessionCreate,
    SessionUpdate,
    MessageModel,
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    SessionResponse,
)
from app.qdrant_client import qdrant_client

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.post(
    "/",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
    description="Create a new chat session to store messages.",
)
def create_session_endpoint(
    db: Session = Depends(get_session),
    session: SessionCreate = Body(...),
):
    """Create a session and return it."""
    new_session = SessionModel(name=session.name)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session details",
    description="Retrieve session information by ID.",
)
def get_session_endpoint(
    db: Session = Depends(get_session),
    session_id: int = Path(..., description="Session ID"),
):
    """Return session info if it exists."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_obj

@router.post(
    "/{session_id}/messages/",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add message",
    description="Add a new message to the specified session.",
)
def create_message_endpoint(
    db: Session = Depends(get_session),
    session_id: int = Path(..., description="Session ID"),
    message: MessageCreate = Body(..., description="Message payload"),
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
    
    # 임베딩 생성 및 저장
    embedding = qdrant_client.get_embedding(message.content)
    qdrant_client.store_embedding(new_message.id, session_id, message.content, embedding)

    return new_message

@router.get(
    "/{session_id}/messages/",
    response_model=List[MessageResponse],
    summary="List session messages",
    description="Retrieve all messages within a session.",
)
def get_messages_endpoint(
    db: Session = Depends(get_session),
    session_id: int = Path(..., description="Session ID"),
):
    """Return messages for a given session."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 메시지 조회
    messages = db.query(MessageModel).filter(MessageModel.session_id == session_id).all()
    return messages


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete session",
    description="Delete a session and all related messages and embeddings.",
)
def delete_session(
    session_id: int = Path(..., description="Session ID"),
    db: Session = Depends(get_session),
):
    """Delete a session and its messages."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.query(MessageModel).filter(MessageModel.session_id == session_id).all()
    for msg in messages:
        qdrant_client.delete_embedding(msg.id)
        db.delete(msg)

    qdrant_client.delete_session_embeddings(session_id)
    db.delete(session_obj)
    db.commit()


@router.put(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Update session",
    description="Modify session information such as its name.",
)
def update_session(
    session_id: int = Path(..., description="Session ID"),
    session: SessionUpdate = Body(...),
    db: Session = Depends(get_session),
):
    """Update session name and return updated session."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.name is not None:
        session_obj.name = session.name
    db.commit()
    db.refresh(session_obj)
    return session_obj


@router.delete(
    "/{session_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete message",
    description="Remove a message from a session and delete its embedding.",
)
def delete_message(
    session_id: int = Path(..., description="Session ID"),
    message_id: int = Path(..., description="Message ID"),
    db: Session = Depends(get_session),
):
    """Delete a message and its embedding."""
    message = (
        db.query(MessageModel)
        .filter(MessageModel.id == message_id, MessageModel.session_id == session_id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    qdrant_client.delete_embedding(message.id)
    db.delete(message)
    db.commit()


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
    db: Session = Depends(get_session),
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

    qdrant_client.delete_embedding(message_obj.id)
    embedding = qdrant_client.get_embedding(message_obj.content)
    qdrant_client.store_embedding(message_obj.id, session_id, message_obj.content, embedding)

    return message_obj
