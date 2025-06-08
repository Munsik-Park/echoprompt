from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
from app.models import (
    SessionModel,
    SemanticSearchRequest,
    SemanticSearchResult,
    SemanticSearchResponse,
    MessageModel,
)
from app.database import get_session, get_db
from app.qdrant_client import QdrantClient, qdrant_client
from app.openai_client import client

# .env 파일 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORGANIZATION_ID")

router = APIRouter(prefix="/query", tags=["Query"])
qdrant_client = QdrantClient()

# OpenAI 클라이언트 초기화
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    organization=os.getenv("OPENAI_ORGANIZATION_ID")
)

async def get_embedding(text: str) -> List[float]:
    """텍스트의 임베딩을 생성합니다."""
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Embedding generation failed",
                "message": str(e),
                "code": "EMBEDDING_ERROR"
            }
        )


@router.post(
    "/semantic_search",
    response_model=SemanticSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic search",
    description="Search messages semantically within a session.",
)
async def semantic_search(request: SemanticSearchRequest, db: Session = Depends(get_db)):
    """세션 내에서 의미 기반 검색을 수행합니다."""
    try:
        # 세션 존재 여부 확인
        session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
        if not session:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Session not found",
                    "message": f"Session with ID {request.session_id} does not exist",
                    "code": "SESSION_NOT_FOUND"
                }
            )

        # 쿼리 임베딩 생성
        query_embedding = await get_embedding(request.query)

        # Qdrant에서 검색
        try:
            search_results = qdrant_client.search_similar(
                query=request.query,
                session_id=request.session_id,
                limit=request.limit
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Qdrant search failed",
                    "message": str(e),
                    "code": "QDRANT_SEARCH_ERROR"
                }
            )

        # 검색 결과가 없는 경우
        if not search_results:
            return SemanticSearchResponse(
                results=[],
                total=0,
                status="success",
                message="No matching results found",
                metadata={
                    "session_id": request.session_id,
                    "query": request.query,
                    "limit": request.limit,
                    "min_score": None,
                    "max_score": None
                }
            )

        # 검색 결과 변환
        results = [
            SemanticSearchResult(
                id=str(result["id"]),
                score=result["score"],
                payload={
                    "content": result["content"],
                    "role": result["role"]
                }
            )
            for result in search_results
        ]

        # 점수 범위 계산
        scores = [result.score for result in results]
        min_score = min(scores) if scores else None
        max_score = max(scores) if scores else None

        return SemanticSearchResponse(
            results=results,
            total=len(results),
            status="success",
            message="Search completed successfully",
            metadata={
                "session_id": request.session_id,
                "query": request.query,
                "limit": request.limit,
                "min_score": min_score,
                "max_score": max_score
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e),
                "code": "INTERNAL_SERVER_ERROR"
            }
        )
