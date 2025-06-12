from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Path, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    SessionModel,
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    MessageModel,
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessagePairResponse,
    ErrorResponse,
    ErrorCode
)
from app.qdrant_client import get_qdrant_client, QdrantClientWrapper
from app.config import settings
from datetime import datetime
from app.openai_client import get_openai_client
import openai

router = APIRouter(
    prefix=f"{settings.API_PREFIX}/sessions",
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
async def delete_session(
    session_id: int, 
    db: Session = Depends(get_db),
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client)
):
    try:
        # 세션 존재 확인
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error=ErrorCode.SESSION_NOT_FOUND,
                    message=f"Session with ID {session_id} not found"
                ).dict()
            )

        # 관련된 모든 메시지 삭제
        db.query(MessageModel).filter(MessageModel.session_id == session_id).delete()
        
        # Qdrant 임베딩 삭제
        qdrant_client.delete_session_embeddings(session_id)
        
        # 세션 삭제
        db.delete(session)
        db.commit()
        
        return {"message": "Session and all related data deleted successfully"}
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
    response_model=MessagePairResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add message",
    description="Add a new message to the specified session.",
)
def create_message_endpoint(
    db: Session = Depends(get_db),
    session_id: int = Path(..., description="Session ID"),
    message: MessageCreate = Body(..., description="Message payload"),
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client),
    openai_client: openai.OpenAI = Depends(get_openai_client)
):
    """Create a message and store its embedding. Also generate LLM response."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # 사용자 메시지 생성
        new_message = MessageModel(session_id=session_id, content=message.content, role=message.role)
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        print(f"[DEBUG] message.content: {message.content}")
        
        if message.role == "user":
            print(f"[DEBUG] 메시지 role: {message.role}")
            print(f"[DEBUG] 메시지 content: {message.content}")
            
            try:
                # 임베딩 생성 및 저장
                print(f"[DEBUG] 임베딩 생성 시작")
                embedding = qdrant_client.get_embedding(message.content)
                qdrant_client._ensure_collection(session_id)
                qdrant_client.store_embedding(
                    message_id=new_message.id,
                    session_id=session_id,
                    content=message.content,
                    embedding=embedding
                )
                print(f"[DEBUG] 임베딩 저장 완료")
                
                # 유사한 메시지 검색
                print(f"[DEBUG] 유사 메시지 검색 시작")
                try:
                    similar_messages = qdrant_client.search_similar(
                        query=message.content,
                        session_id=session_id,
                        limit=5
                    )
                    print(f"[DEBUG] 검색된 메시지 수: {len(similar_messages)}")
                    print(f"[DEBUG] 검색 결과 상세: {similar_messages}")
                    
                    context = "\n".join([msg["payload"]["content"] for msg in similar_messages if "content" in msg["payload"]])
                    print(f"[DEBUG] 최종 컨텍스트: {context}")
                except Exception as e:
                    print(f"[ERROR] 유사 메시지 검색 중 에러: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to search similar messages: {str(e)}"
                    )
                
                # LLM 응답 생성
                print(f"[DEBUG] OpenAI API 호출 시작")
                try:
                    print(f"[DEBUG] API 요청 파라미터:")
                    print(f"- 모델: gpt-3.5-turbo")
                    print(f"- 컨텍스트: {context}")
                    print(f"- 사용자 메시지: {message.content}")
                    
                    response = openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": f"Context: {context}\n\nUser: {message.content}"}
                        ]
                    )
                    print(f"[DEBUG] OpenAI API 응답 성공")
                    print(f"[DEBUG] 응답 객체: {response}")
                    print(f"[DEBUG] LLM 응답 내용: {response.choices[0].message.content}")
                except Exception as e:
                    print(f"[ERROR] OpenAI API 호출 중 에러: {str(e)}")
                    print(f"[ERROR] 에러 타입: {type(e)}")
                    print(f"[ERROR] 에러 상세: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to generate LLM response: {str(e)}"
                    )
                
                # 응답 메시지 저장
                print(f"[DEBUG] 응답 메시지 저장 시작")
                assistant_message = MessageModel(
                    session_id=session_id,
                    content=response.choices[0].message.content,
                    role="assistant"
                )
                db.add(assistant_message)
                db.commit()
                db.refresh(assistant_message)
                print(f"[DEBUG] 응답 메시지 저장 완료")
                
                # 사용자 메시지와 어시스턴트 메시지를 모두 반환
                return {
                    "message": assistant_message,
                    "user_message": new_message
                }
                
            except Exception as e:
                print(f"[ERROR] LLM 응답 생성 중 에러 발생: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate LLM response: {str(e)}"
                )
        
        return new_message
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

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
