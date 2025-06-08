import os
import openai
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session

from app.database import get_session
from app.models import ChatRequest, ChatResponse, MessageModel, SessionModel
from app.qdrant_client import qdrant_client

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with LLM",
    description="Send a prompt to the LLM and store the assistant response in the session.",
)
def chat_endpoint(request: ChatRequest = Body(...), db: Session = Depends(get_session)):
    """Call the LLM with a user prompt and store the response."""
    session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": request.prompt}],
    )
    content = response.choices[0].message["content"]

    message = MessageModel(session_id=request.session_id, content=content, role="assistant")
    db.add(message)
    db.commit()
    db.refresh(message)

    embedding = qdrant_client.get_embedding(content)
    qdrant_client.store_embedding(message.id, request.session_id, content, embedding)

    return ChatResponse(message=content)
