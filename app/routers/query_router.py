from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
import openai
import os
from dotenv import load_dotenv
from app.models import (
    SessionModel,
    SemanticSearchRequest,
    SemanticSearchResult,
    SemanticSearchResponse,
)
from app.database import get_session
from app.qdrant_client import QdrantClient

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter(prefix="/query", tags=["query"])
qdrant_client = QdrantClient()

async def get_embedding(text: str) -> List[float]:
    """텍스트의 임베딩 벡터 생성"""
    response = await openai.Embedding.acreate(
        input=text,
        model="text-embedding-ada-002"
    )
    return response["data"][0]["embedding"]


@router.post("/semantic_search", response_model=SemanticSearchResponse)
def semantic_search(
    request: SemanticSearchRequest, db: Session = Depends(get_session)
):
    """Perform semantic search within a session."""
    result = db.exec(select(SessionModel).where(SessionModel.id == request.session_id))
    session = result.first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    query_embedding = qdrant_client.get_embedding(request.query)

    results = qdrant_client.search_similar(
        query_embedding=query_embedding,
        session_id=request.session_id,
        limit=request.limit,
    )

    formatted = [
        SemanticSearchResult(content=r.payload.get("content", ""), score=r.score)
        for r in results
    ]
    return SemanticSearchResponse(results=formatted)
