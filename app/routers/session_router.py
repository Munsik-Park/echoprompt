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
    MessageTreeNode,
    DocumentMessageGroup,
    SessionDocumentTreeResponse,
    ErrorResponse,
    ErrorCode,
    UserModel # Added for fetching user_identifier
    # SessionModel is already imported
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

from collections import defaultdict

@router.get(
    "/{session_id}/tree",
    response_model=SessionDocumentTreeResponse, # Changed response model
    summary="Get message tree for a session, grouped by document_id",
    description="Retrieve all messages for a session, grouped by document_id and sorted by creation date within each group.",
)
async def get_message_tree(
    session_id: int = Path(..., description="Session ID"),
    db: Session = Depends(get_db),
):
    # Check if session exists
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error=ErrorCode.SESSION_NOT_FOUND,
                message=f"Session with ID {session_id} not found"
            ).dict()
        )

    # Fetch messages from the database for the session
    db_messages = db.query(MessageModel).filter(MessageModel.session_id == session_id).order_by(MessageModel.document_id, MessageModel.created_at).all()

    # Group messages by document_id
    message_groups = defaultdict(list)
    for msg in db_messages:
        doc_id = msg.document_id if msg.document_id is not None else "unknown_document"
        message_groups[doc_id].append(msg)

    # Convert grouped messages to response model structure
    document_message_groups = []
    for doc_id, messages_in_group in message_groups.items():
        # Messages are already sorted by created_at due to the ORDER BY clause,
        # but if we didn't sort by document_id initially, we would sort here.
        # For clarity, we can re-sort if needed, or rely on the DB sort.
        # messages_in_group.sort(key=lambda m: m.created_at) # Already sorted by DB

        tree_nodes = []
        for msg_model in messages_in_group:
            tree_nodes.append(MessageTreeNode(
                id=msg_model.id,
                session_id=msg_model.session_id,
                # document_id=msg_model.document_id, # MessageTreeNode does not have document_id, it's one level up
                content=msg_model.content,
                role=msg_model.role,
                created_at=msg_model.created_at,
                updated_at=msg_model.updated_at,
                children=[] # Still flat within the document group
            ))

        document_message_groups.append(DocumentMessageGroup(
            document_id=doc_id,
            messages=tree_nodes
        ))

    return SessionDocumentTreeResponse(__root__=document_message_groups)

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
        new_message = MessageModel(
            session_id=session_id,
            content=message.content,
            role=message.role,
            document_id=message.document_id # Save document_id
        )
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

                # Fetch user_identifier for Qdrant before storing embedding
                user_identifier_for_qdrant = None
                db_session_for_user = db.query(SessionModel).filter(SessionModel.id == new_message.session_id).first()
                if db_session_for_user and db_session_for_user.user_id:
                    db_user = db.query(UserModel).filter(UserModel.id == db_session_for_user.user_id).first()
                    if db_user:
                        user_identifier_for_qdrant = db_user.user_identifier

                qdrant_client.store_embedding(
                    message_id=new_message.id,
                    session_id=new_message.session_id,
                    content=message.content,
                    embedding=embedding,
                    document_id=new_message.document_id,
                    user_identifier=user_identifier_for_qdrant,
                    memory_type=message.memory_type or "short_term" # Pass memory_type
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
    if message.document_id is not None: # Save document_id
        message_obj.document_id = message.document_id

    db.commit()
    db.refresh(message_obj)

    # 임베딩 재생성
    if message.content is not None and message_obj.role == "user":
        embedding = qdrant_client.get_embedding(message.content)

        # Fetch user_identifier for Qdrant before storing embedding
        user_identifier_for_qdrant = None
        db_session_for_user = db.query(SessionModel).filter(SessionModel.id == message_obj.session_id).first()
        if db_session_for_user and db_session_for_user.user_id:
            db_user = db.query(UserModel).filter(UserModel.id == db_session_for_user.user_id).first()
            if db_user:
                user_identifier_for_qdrant = db_user.user_identifier

        qdrant_client.store_embedding(
            message_id=message_id,
            session_id=message_obj.session_id,
            content=message.content, # This is the new content from the request
            embedding=embedding,
            document_id=message_obj.document_id, # document_id is part of the message identity, not changed here
            user_identifier=user_identifier_for_qdrant,
            memory_type=message.memory_type if message.memory_type is not None else "short_term" # Pass memory_type
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
