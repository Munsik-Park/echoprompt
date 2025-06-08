import os
import openai
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_session, get_db
from app.models import ChatRequest, ChatResponse, MessageModel, SessionModel

load_dotenv()

router = APIRouter(tags=["Chat"])

class ChatRequest(BaseModel):
    session_id: int
    prompt: str

class ChatResponse(BaseModel):
    message: str
    message_id: Optional[int] = None

# OpenAI API 설정
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORGANIZATION_ID")

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with LLM",
    description="Send a prompt to the LLM and store the assistant response in the session.",
)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Call the LLM with a user prompt and store the response."""
    try:
        # 세션 존재 여부 확인
        session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # 사용자 메시지 저장
        user_message = MessageModel(
            session_id=request.session_id,
            role="user",
            content=request.prompt
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        try:
            # OpenAI API 호출 (새로운 버전)
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": request.prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            assistant_content = response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API 호출 중 에러 발생: {str(e)}")
            # 에러 발생 시 기본 응답 생성
            assistant_content = "죄송합니다. 응답을 생성하는 중에 문제가 발생했습니다."

        # 응답 메시지 저장
        assistant_message = MessageModel(
            session_id=request.session_id,
            role="assistant",
            content=assistant_content
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        return ChatResponse(
            message=assistant_message.content,
            message_id=assistant_message.id
        )

    except Exception as e:
        print(f"Chat 엔드포인트 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
