from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models import (
    SessionModel,
    MessageModel,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    ErrorCode,
    UserModel, # Added for fetching user_identifier
    RetrievedChunk # Import for response
)
from app.qdrant_client import get_qdrant_client, QdrantClientWrapper
from app.openai_client import get_openai_client
from app.config import settings

router = APIRouter(
    prefix=f"{settings.API_PREFIX}/chat",
    tags=["Chat"]
)

@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with LLM",
    description="Send a prompt to the LLM and store the assistant response in the session.",
)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client),
    openai_client = Depends(get_openai_client)
):
    """채팅 요청을 처리하고 응답을 생성합니다."""
    try:
        # 세션 존재 여부 확인
        session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # 사용자 메시지 저장
        user_message = MessageModel(
            session_id=request.session_id,
            content=request.prompt,
            role="user",
            document_id=request.document_id # Save document_id
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        # 임베딩 생성 및 저장
        embedding = qdrant_client.get_embedding(request.prompt)

        # Fetch user_identifier for Qdrant
        user_identifier_for_qdrant = None
        # session is already fetched: session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
        if session and session.user_id:
            db_user = db.query(UserModel).filter(UserModel.id == session.user_id).first()
            if db_user:
                user_identifier_for_qdrant = db_user.user_identifier

        qdrant_client.store_embedding(
            message_id=user_message.id,
            session_id=request.session_id, # This is session.id
            content=request.prompt,
            embedding=embedding,
            document_id=user_message.document_id, # Ensure user_message has this from request.document_id
            user_identifier=user_identifier_for_qdrant,
            memory_type=request.memory_type or "short_term" # Pass memory_type
        )

        # 유사한 메시지 검색 (using multi-stage search)
        similar_messages = qdrant_client.multi_stage_search(
            query=request.prompt,
            session_id=request.session_id, # DB session.id
            user_identifier=user_identifier_for_qdrant, # Pass user_identifier
            limit_per_stage=3 # Hardcoded limit_per_stage for chat context
            # short_term_days_cutoff can be configured globally or passed if added to ChatRequest
        )

        # 컨텍스트 구성
        # The payload structure from multi_stage_search is List[Dict{"id": ..., "score": ..., "payload": ...}]
        # Access content via msg["payload"]["content"]
        context_parts = []
        for msg in similar_messages:
            if msg and "payload" in msg and isinstance(msg["payload"], dict) and "content" in msg["payload"]:
                context_parts.append(str(msg["payload"]["content"]))
        context = "\n".join(context_parts)

        # OpenAI API 호출
        response = openai_client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Context: {context}\n\nUser: {request.prompt}"}
            ]
        )

        # 응답 메시지 저장
        assistant_message = MessageModel(
            session_id=request.session_id,
            content=response.choices[0].message.content,
            role="assistant",
            document_id=request.document_id # Save document_id for assistant message too?
                                            # Or should assistant messages have null document_id?
                                            # For now, let's assume it inherits from the user prompt context.
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        retrieved_chunks_for_response: Optional[List[RetrievedChunk]] = None
        if similar_messages: # similar_messages is the result from multi_stage_search
            retrieved_chunks_for_response = []
            for chunk_data in similar_messages:
                payload = chunk_data.get("payload") if chunk_data.get("payload") is not None else {}
                retrieved_chunks_for_response.append(
                    RetrievedChunk(
                        id=chunk_data.get("id", "N/A"), # Ensure ID is present or default
                        content=str(payload.get("content")) if payload.get("content") is not None else None,
                        score=float(chunk_data.get("score", 0.0)), # Ensure score is float
                        document_id=str(payload.get("document_id")) if payload.get("document_id") is not None else None,
                        memory_type=str(payload.get("memory_type")) if payload.get("memory_type") is not None else None,
                        payload=payload
                    )
                )

        return ChatResponse(
            message=assistant_message.content,
            retrieved_chunks=retrieved_chunks_for_response
            # old similar_messages field is removed by this change
        )

    except Exception as e:
        print(f"Chat 엔드포인트 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client),
    openai_client = Depends(get_openai_client)
):
    """채팅 요청을 처리하고 응답을 생성합니다."""
    try:
        # 세션 존재 여부 확인
        session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # 사용자 메시지 저장
        user_message = MessageModel(
            session_id=request.session_id,
            content=request.prompt,
            role="user"
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        # OpenAI API 호출
        response = openai_client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.prompt}
            ]
        )

        # 응답 메시지 저장
        assistant_message = MessageModel(
            session_id=request.session_id,
            content=response.choices[0].message.content,
            role="assistant"
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        return ChatResponse(
            message=assistant_message.content,
            similar_messages=[]
        )

    except Exception as e:
        print(f"Chat 엔드포인트 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
