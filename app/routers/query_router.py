from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
import openai
import os
from dotenv import load_dotenv
from app.models import SessionModel, MessageModel, SemanticSearchRequest, SemanticSearchResponse
from app.database import get_session
from app.qdrant_client import QdrantClient

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter(prefix="/query", tags=["query"])
qdrant_client = QdrantClient()

class QueryRequest(BaseModel):
    query: str
    session_id: int
    top_k: int = 3

class QueryResponse(BaseModel):
    messages: List[dict]
    scores: List[float]

async def get_embedding(text: str) -> List[float]:
    """텍스트의 임베딩 벡터 생성"""
    response = await openai.Embedding.acreate(
        input=text,
        model="text-embedding-ada-002"
    )
    return response["data"][0]["embedding"]

@router.post("/query/", response_model=QueryResponse)
def semantic_search(request: QueryRequest, db: Session = Depends(get_session)):
    """의미적 검색을 수행합니다."""
    # 세션 존재 여부 확인
    result = db.exec(select(SessionModel).where(SessionModel.id == request.session_id))
    session = result.first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 쿼리 임베딩 생성
    query_embedding = qdrant_client.get_embedding(request.query)
    
    # 유사 메시지 검색
    results = qdrant_client.search_similar(
        query_embedding=query_embedding,
        session_id=request.session_id,
        top_k=request.top_k
    )
    
    # 결과 포맷팅
    messages = [{"content": r.content, "role": r.role} for r in results]
    scores = [r.score for r in results]
    
    return QueryResponse(messages=messages, scores=scores)

@router.post("/semantic-search", response_model=SemanticSearchResponse)
def semantic_search(request: SemanticSearchRequest, db: Session = Depends(get_session)):
    """의미적 검색을 수행합니다."""
    # 세션 존재 여부 확인
    result = db.exec(select(SessionModel).where(SessionModel.id == request.session_id))
    session = result.first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 쿼리 임베딩 생성
    query_embedding = qdrant_client.get_embedding(request.query)
    
    # 유사 메시지 검색
    results = qdrant_client.search_similar(
        query_embedding=query_embedding,
        session_id=request.session_id,
        top_k=request.limit
    )
    
    # 결과 포맷팅
    messages = [r.content for r in results]
    return SemanticSearchResponse(messages=messages) 