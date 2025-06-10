from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models.session import SessionModel
from app.models.message import MessageModel
from app.models.chat import ChatRequest, ChatResponse
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
            role="user"
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        # 임베딩 생성 및 저장
        embedding = qdrant_client.get_embedding(request.prompt)
        qdrant_client.store_embedding(
            message_id=user_message.id,
            session_id=request.session_id,
            content=request.prompt,
            embedding=embedding
        )

        # 유사한 메시지 검색
        similar_messages = qdrant_client.search_similar(
            query=request.prompt,
            session_id=request.session_id,
            limit=5
        )

        # 컨텍스트 구성
        context = "\n".join([msg["content"] for msg in similar_messages])

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
            role="assistant"
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        return ChatResponse(
            message=assistant_message.content,
            similar_messages=[msg["content"] for msg in similar_messages]
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
    # 실제 채팅 처리 로직을 여기에 구현
    # 예시: openai_client를 사용해 답변 생성 등
    try:
        # ... (기존 로직)
        return ChatResponse(message="답변 예시")
    except Exception as e:
        print(f"Chat 엔드포인트 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
