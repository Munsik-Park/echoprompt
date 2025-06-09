from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.models import (
    SessionModel,
    SemanticSearchRequest,
    SemanticSearchResult,
    SemanticSearchResponse,
    MessageModel,
)
from app.models.error import ErrorResponse, ErrorCode
from app.database import get_db
from app.qdrant_client import get_qdrant_client, QdrantClientWrapper
from app.openai_client import get_openai_client
from app.models.query import QueryRequest, QueryResponse

router = APIRouter(
    prefix="/api/v1/query",
    tags=["Query"]
)

@router.post(
    "/semantic_search",
    response_model=SemanticSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic search",
    description="Search messages semantically within a session.",
)
async def semantic_search(
    request: SemanticSearchRequest,
    db: Session = Depends(get_db),
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client),
    openai_client = Depends(get_openai_client)
):
    """세션 내에서 의미 기반 검색을 수행합니다."""
    try:
        # 세션 존재 여부 확인
        session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error=ErrorCode.SESSION_NOT_FOUND,
                    message=f"Session with ID {request.session_id} not found"
                ).dict()
            )

        # 쿼리 임베딩 생성
        try:
            response = openai_client.embeddings.create(
                input=request.query,
                model="text-embedding-ada-002"
            )
            query_embedding = response.data[0].embedding
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error=ErrorCode.EMBEDDING_ERROR,
                    message="Failed to generate embedding for query",
                    details={"error": str(e)}
                ).dict()
            )

        # Qdrant에서 검색
        try:
            search_results = qdrant_client.search_similar(
                query=request.query,
                session_id=request.session_id,
                limit=request.limit
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error=ErrorCode.QDRANT_ERROR,
                    message="Failed to perform semantic search",
                    details={"error": str(e)}
                ).dict()
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.INTERNAL_SERVER_ERROR,
                message="An unexpected error occurred",
                details={"error": str(e)}
            ).dict()
        )

@router.post("/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client)
):
    """세션 내에서 유사한 메시지를 검색합니다."""
    try:
        # 세션 존재 확인
        session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error=ErrorCode.SESSION_NOT_FOUND,
                    message=f"Session with ID {request.session_id} not found"
                ).dict()
            )
        
        # 유사한 메시지 검색
        try:
            similar_messages = qdrant_client.search_similar(
                query=request.query,
                session_id=request.session_id,
                limit=request.limit
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error=ErrorCode.QDRANT_ERROR,
                    message="Failed to perform semantic search",
                    details={"error": str(e)}
                ).dict()
            )
        
        return QueryResponse(
            messages=[msg["content"] for msg in similar_messages],
            scores=[msg["score"] for msg in similar_messages]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error=ErrorCode.INTERNAL_SERVER_ERROR,
                message="An unexpected error occurred",
                details={"error": str(e)}
            ).dict()
        )

@router.get("/search")
async def semantic_search(
    query: str,
    session_id: int,
    limit: int = 5,
    qdrant_client: QdrantClientWrapper = Depends(get_qdrant_client)
):
    """Perform semantic search on messages in a session."""
    results = qdrant_client.search(
        query=query,
        session_id=session_id,
        limit=limit
    )
    return results
