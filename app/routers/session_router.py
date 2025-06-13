from typing import List, Dict, Optional # Added Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Path, status
from sqlalchemy.orm import Session
from sqlalchemy import asc
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
from app.models.tree import MessageNode, SessionMessageTreeResponse # Added tree models
from app.qdrant_client import get_qdrant_client, QdrantClientWrapper
from app.config import settings
from datetime import datetime
from app.openai_client import get_openai_client

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

# Helper function to convert MessageModel to MessageNode
# This can be expanded if there are more complex mapping needs
def convert_message_to_node(message: MessageModel) -> MessageNode:
    return MessageNode.model_validate(message)

@router.get("/{session_id}/tree", response_model=SessionMessageTreeResponse)
async def get_session_message_tree(session_id: int, db: Session = Depends(get_db)):
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

        db_messages = db.query(MessageModel)\
            .filter(MessageModel.session_id == session_id)\
            .order_by(asc(MessageModel.created_at))\
            .all()

        if not db_messages:
            return []

        # Group messages by document_id
        grouped_by_doc_id: Dict[Optional[str], List[MessageNode]] = {}
        for msg in db_messages:
            node = convert_message_to_node(msg)
            doc_id = msg.document_id # This will be None if not set
            grouped_by_doc_id.setdefault(doc_id, []).append(node)

        response_nodes: List[MessageNode] = []

        # Process groups
        for doc_id, child_message_nodes in grouped_by_doc_id.items():
            if doc_id is None:
                # Messages with no document_id become root nodes directly
                response_nodes.extend(child_message_nodes)
            else:
                # For messages with a document_id, create a conceptual parent node
                # This parent node represents the document/group.
                # Its details can be synthetic or based on the first child.
                if child_message_nodes: # Ensure there are messages in the group
                    parent_node = MessageNode(
                        id=0, # Synthetic ID for the group node
                        content=f"Document Group: {doc_id}",
                        role="system", # Or some other role indicating it's a group
                        created_at=child_message_nodes[0].created_at, # Use first child's timestamp
                        user_id=None, # Or derive if meaningful
                        document_id=doc_id,
                        memory_type="group_summary", # Example memory_type
                        children=child_message_nodes
                    )
                    response_nodes.append(parent_node)

        # Sort root nodes by created_at timestamp of their first effective message
        # For conceptual parents, it's their own created_at. For direct messages, it's their created_at.
        response_nodes.sort(key=lambda n: n.created_at)

        return response_nodes

    except HTTPException:
        raise
    except Exception as e:
        # Log the error for debugging
        # import traceback
        # print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.DATABASE_ERROR, # Or a more specific error code
                message="Failed to retrieve or build session message tree",
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
    openai_client = Depends(get_openai_client)
):
    """Create a message and store its embedding. Also generate LLM response."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # 사용자 메시지 생성
        # Include new fields from MessageCreate model
        new_message_db = MessageModel(
            session_id=session_id,
            content=message.content,
            role=message.role,
            user_id=message.user_id,
            document_id=message.document_id,
            memory_type=message.memory_type
        )
        db.add(new_message_db)
        db.commit()
        db.refresh(new_message_db)
        # print(f"[DEBUG] message.content: {message.content}") # Original debug

        retrieved_chunks_for_response = [] # Initialize for response
        
        if message.role == "user":
            # print(f"[DEBUG] 메시지 role: {message.role}") # Original debug
            # print(f"[DEBUG] 메시지 content: {message.content}") # Original debug
            
            try:
                # 임베딩 생성 및 저장
                # print(f"[DEBUG] 임베딩 생성 시작") # Original debug
                embedding = qdrant_client.get_embedding(message.content)
                qdrant_client._ensure_collection(session_id) # Ensure collection exists for session
                qdrant_client.store_embedding(
                    message_id=new_message_db.id,
                    session_id=session_id,
                    content=message.content,
                    embedding=embedding,
                    user_id=message.user_id,       # Pass new field
                    document_id=message.document_id, # Pass new field
                    memory_type=message.memory_type  # Pass new field
                )
                # print(f"[DEBUG] 임베딩 저장 완료") # Original debug
                
                # 유사한 메시지 검색
                # print(f"[DEBUG] 유사 메시지 검색 시작") # Original debug
                try:
                    # Pass user_id, document_id, memory_type to search_similar for filtering
                    similar_messages = qdrant_client.search_similar(
                        query=message.content,
                        session_id=session_id,
                        limit=5, # Keep limit or make it configurable
                        user_id=message.user_id,
                        document_id=message.document_id,
                        memory_type=message.memory_type
                    )
                    retrieved_chunks_for_response = similar_messages # Store for response
                    # print(f"[DEBUG] 검색된 메시지 수: {len(similar_messages)}") # Original debug
                    # print(f"[DEBUG] 검색 결과 상세: {similar_messages}") # Original debug
                    
                    context = "\n".join([msg["payload"]["content"] for msg in similar_messages if msg.get("payload", {}).get("content")])
                    # print(f"[DEBUG] 최종 컨텍스트: {context}") # Original debug
                except Exception as e:
                    # print(f"[ERROR] 유사 메시지 검색 중 에러: {str(e)}") # Original debug
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
                # print(f"[DEBUG] 응답 메시지 저장 시작") # Original debug
                assistant_message_db = MessageModel(
                    session_id=session_id,
                    content=response.choices[0].message.content,
                    role="assistant"
                    # Potentially set user_id, document_id, memory_type for assistant message if needed
                )
                db.add(assistant_message_db)
                db.commit()
                db.refresh(assistant_message_db)
                # print(f"[DEBUG] 응답 메시지 저장 완료") # Original debug
                
                # Convert DB models to Pydantic response models
                new_message_response = MessageResponse.model_validate(new_message_db)
                assistant_message_response = MessageResponse.model_validate(assistant_message_db)

                return MessagePairResponse(
                    user_message=new_message_response,
                    message=assistant_message_response, # 'message' is the assistant's message in MessagePairResponse
                    retrieved_chunks=retrieved_chunks_for_response
                )
                
            except Exception as e:
                # print(f"[ERROR] LLM 응답 생성 중 에러 발생: {str(e)}") # Original debug
                # Consider more specific error logging/handling
                raise HTTPException(
                    status_code=500, # Or a more specific error code
                    detail=f"Failed to process message and generate LLM response: {str(e)}"
                )
        
        # If not user role, just return the created message (e.g. if assistant message posted directly)
        # This part of logic might need review based on use-case for non-user roles
        new_message_response = MessageResponse.model_validate(new_message_db)
        return MessagePairResponse(
            user_message=new_message_response, # Or handle appropriately if this isn't a user message
            message=new_message_response, # This is problematic, MessagePairResponse expects user and assistant.
                                          # This path should ideally not be hit if flow is user -> assistant.
                                          # For now, to satisfy response model, providing something.
                                          # Consider raising error or specific response for non-user initial messages.
            retrieved_chunks=[] # No chunks if not user message flow
        )

    except Exception as e:
        db.rollback()
        # print(f"[ERROR] Outer exception in create_message_endpoint: {str(e)}") # Original debug
        raise HTTPException(status_code=500, detail=f"Outer error in message creation: {str(e)}")

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
