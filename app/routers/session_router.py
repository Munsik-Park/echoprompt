from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body, Path
from sqlmodel import Session, select
from app.database import get_session
from app.models import (
    SessionModel,
    SessionCreate,
    MessageModel,
    MessageCreate,
    MessageResponse,
    SessionResponse,
)
from app.qdrant_client import qdrant_client

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/sessions/", response_model=SessionResponse)
def create_session_endpoint(db: Session = Depends(get_session)):
    """새로운 세션을 생성합니다."""
    session = SessionModel()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session_endpoint(db: Session = Depends(get_session), session_id: int = Path(..., description="세션 ID")):
    """세션 정보를 조회합니다."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_obj

@router.post("/sessions/{session_id}/messages/", response_model=MessageResponse)
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
    qdrant_client.store_embedding(new_message.id, embedding, session_id, message.content, message.role)
    
    return new_message

@router.get("/sessions/{session_id}/messages/", response_model=List[MessageResponse])
def get_messages_endpoint(db: Session = Depends(get_session), session_id: int = Path(..., description="세션 ID")):
    """세션의 모든 메시지를 조회합니다."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 메시지 조회
    messages = db.query(MessageModel).filter(MessageModel.session_id == session_id).all()
    return messages 