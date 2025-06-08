from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body, Path
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

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=SessionResponse)
def create_session_endpoint(
    db: Session = Depends(get_session),
    session: SessionCreate = Body(...)
):
    """새로운 세션을 생성합니다."""
    new_session = SessionModel(name=session.name)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get("/{session_id}", response_model=SessionResponse)
def get_session_endpoint(db: Session = Depends(get_session), session_id: int = Path(..., description="세션 ID")):
    """세션 정보를 조회합니다."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_obj

@router.post("/{session_id}/messages/", response_model=MessageResponse)
def create_message_endpoint(db: Session = Depends(get_session), session_id: int = Path(..., description="세션 ID"), message: MessageCreate = Body(..., description="The message to add")):
    """세션에 새로운 메시지를 추가합니다."""
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

@router.get("/{session_id}/messages/", response_model=List[MessageResponse])
def get_messages_endpoint(db: Session = Depends(get_session), session_id: int = Path(..., description="세션 ID")):
    """세션의 모든 메시지를 조회합니다."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 메시지 조회
    messages = db.query(MessageModel).filter(MessageModel.session_id == session_id).all()
    return messages


@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: int = Path(..., description="세션 ID"),
    db: Session = Depends(get_session),
):
    """Delete a session and related data."""
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


@router.put("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: int = Path(..., description="세션 ID"),
    session: SessionUpdate = Body(...),
    db: Session = Depends(get_session),
):
    """Update session information."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.name is not None:
        session_obj.name = session.name
    db.commit()
    db.refresh(session_obj)
    return session_obj


@router.delete("/{session_id}/messages/{message_id}", status_code=204)
def delete_message(
    session_id: int = Path(..., description="세션 ID"),
    message_id: int = Path(..., description="메시지 ID"),
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


@router.put("/{session_id}/messages/{message_id}", response_model=MessageResponse)
def update_message(
    session_id: int = Path(..., description="세션 ID"),
    message_id: int = Path(..., description="메시지 ID"),
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
