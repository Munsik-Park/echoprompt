from typing import List
from fastapi import APIRouter, HTTPException, Depends, status, Request, Form
from sqlalchemy.orm import Session
from app.models import (
    SessionModel,
    MessageModel,
    QueryRequest,
    QueryResponse,
    SemanticSearchRequest,
    SemanticSearchResult,
    SemanticSearchResponse,
    ErrorResponse,
    ErrorCode
)
from app.database import get_db
from app.qdrant_client import get_qdrant_client, QdrantClientWrapper
from app.openai_client import get_openai_client
from app.config import settings

router = APIRouter(
    prefix=f"{settings.API_PREFIX}/query",
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
        # 디버그 로깅 추가
        print(f"[DEBUG] 요청 데이터:")
        print(f"- session_id: {request.session_id}")
        print(f"- query: {request.query}")
        print(f"- limit: {request.limit}")
        print(f"- request type: {type(request)}")
        print(f"- request dict: {request.dict()}")

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
            print(f"임베딩 모델: {settings.OPENAI_EMBEDDING_MODEL}")
            response = openai_client.embeddings.create(
                input=request.query,
                model=settings.OPENAI_EMBEDDING_MODEL
            )
            query_embedding = response.data[0].embedding
        except Exception as e:
            print(f"임베딩 생성 에러: {str(e)}")
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
            # Use multi_stage_search instead of search_similar
            search_results = qdrant_client.multi_stage_search(
                query=request.query,
                session_id=request.session_id, # DB session.id
                user_identifier=request.user_identifier, # Pass user_identifier
                limit_per_stage=request.limit # Use request.limit as limit_per_stage
                # short_term_days_cutoff can be added to SemanticSearchRequest if needed
            )
            print(f"Multi-stage 검색 결과: {search_results}")
        except Exception as e:
            print(f"Qdrant 검색 에러: {str(e)}")
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
        results = []
        for result in search_results:
            try:
                payload = result.get("payload", {})
                search_result = SemanticSearchResult(
                    id=str(result.get("id")),
                    score=float(result.get("score", 0.0)),
                    payload={
                        "content": str(payload.get("content", "")),
                        "role": str(payload.get("role", "unknown"))
                    }
                )
                results.append(search_result)
            except Exception as e:
                print(f"결과 변환 에러: {str(e)}, 결과: {result}")
                continue

        # 점수 범위 계산
        scores = [result.score for result in results]
        min_score = min(scores) if scores else None
        max_score = max(scores) if scores else None

        # 전체 검색 결과 수 계산 (limit 제한 없이) - This part might be less relevant with multi-stage
        # as 'total' usually means total matchable before limit. Multi-stage complicates this.
        # For now, let's define total as the count of de-duplicated results from multi_stage_search without a final limit.
        # Or, we can sum limits if that's meaningful.
        # Let's simplify: total returned by the current multi_stage_search call.
        # The multi_stage_search already returns a combined list.
        # If we want a "true total available", that's a more complex query.
        # For now, total = len(search_results) after multi-stage combination and de-duplication.
        total_count = len(search_results)

        response = SemanticSearchResponse(
            results=results,
            total=total_count,
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
        return response
    except HTTPException:
        raise
    except Exception as e:
        print(f"의미 검색 에러: {str(e)}")
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
            # Use multi_stage_search instead of search_similar
            similar_messages = qdrant_client.multi_stage_search(
                query=request.query,
                session_id=request.session_id, # DB session.id
                user_identifier=request.user_identifier, # Pass user_identifier
                limit_per_stage=request.limit # Use request.limit as limit_per_stage
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
