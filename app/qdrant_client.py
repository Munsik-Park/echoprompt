import os
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from app.models import VectorPayload
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv
import requests
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
import openai
from app.openai_client import get_openai_client
from app.config import settings

# 환경 변수 로드
load_dotenv()

# Qdrant 클라이언트 설정
qdrant_config = {
    "QDRANT_URL": settings.QDRANT_URL
}

def validate_env_vars():
    """환경 변수 검증"""
    required_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "OPENAI_ORGANIZATION_ID": os.getenv("OPENAI_ORGANIZATION_ID"),
        "QDRANT_URL": os.getenv("QDRANT_URL", "http://localhost:6333")
    }
    
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return required_vars

# 환경 변수 검증 및 설정
env_vars = validate_env_vars()
QDRANT_URL = env_vars["QDRANT_URL"]
OPENAI_API_KEY = env_vars["OPENAI_API_KEY"]
OPENAI_ORG_ID = env_vars["OPENAI_ORGANIZATION_ID"]
COLLECTION_NAME = "echoprompt_messages"

class QdrantClientWrapper:
    def __init__(self, url: str, openai_client: Optional[openai.OpenAI] = None):
        self._openai_client = openai_client
        self.client = QdrantClient(url=url)

    @property
    def openai_client(self) -> openai.OpenAI:
        if self._openai_client is None:
            self._openai_client = get_openai_client()
        return self._openai_client

    def _ensure_collection(self, session_id: int) -> None:
        collection_name = f"session_{session_id}"
        try:
            self.client.get_collection(collection_name=collection_name)
        except Exception:
            try:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=1536,  # OpenAI ada-002 모델의 임베딩 크기
                        distance=models.Distance.COSINE
                    )
                )
            except Exception as e:
                # 409 Conflict(이미 존재) 에러는 무시
                if "already exists" in str(e) or "409" in str(e):
                    pass
                else:
                    raise

    def get_embedding(self, text: str) -> List[float]:
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding

    def store_embedding(
        self,
        message_id: int,
        session_id: int,
        content: str,
        embedding: List[float],
        document_id: Optional[str] = None,
        user_identifier: Optional[str] = None, # For user_id in Qdrant
        memory_type: Literal["short_term", "long_term", "summary"] = "short_term" # Changed to Literal
    ) -> None:
        self._ensure_collection(session_id)
        collection_name = f"session_{session_id}"
        
        self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=message_id,
                    vector=embedding,
                    payload={
                        "content": content,
                        "message_id": message_id,
                        "session_id": session_id, # This is the DB session.id (integer)
                        "document_id": document_id,
                        "user_id": user_identifier, # This is the user_identifier (string)
                        "memory_type": memory_type # New field in payload
                    }
                )
            ]
        )

    def delete_embedding(self, message_id: int, session_id: int) -> None:
        collection_name = f"session_{session_id}"
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=[message_id]
                )
            )
        except Exception as e:
            print(f"Error deleting embedding: {e}")

    def delete_session_embeddings(self, session_id: int) -> None:
        collection_name = f"session_{session_id}"
        try:
            # 컬렉션 자체를 삭제
            self.client.delete_collection(collection_name=collection_name)
            print(f"Collection {collection_name} deleted successfully")
        except Exception as e:
            print(f"Error deleting session embeddings: {e}")
            # 컬렉션이 없는 경우는 무시
            if "not found" not in str(e).lower():
                raise

    def delete_embeddings_by_filter(self, session_id: int, filter_conditions: Dict[str, Any]) -> None:
        """특정 조건에 맞는 임베딩들을 삭제합니다."""
        collection_name = f"session_{session_id}"
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=value)
                            )
                            for key, value in filter_conditions.items()
                        ]
                    )
                )
            )
        except Exception as e:
            print(f"Error deleting embeddings by filter: {e}")

    def delete_embeddings_by_similarity(self, session_id: int, query: str, similarity_threshold: float) -> None:
        """특정 쿼리와의 유사도가 임계값 이하인 임베딩들을 삭제합니다."""
        collection_name = f"session_{session_id}"
        try:
            query_embedding = self.get_embedding(query)
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=100  # 충분히 큰 수로 설정
            )
            
            # 임계값 이하의 점수를 가진 포인트 ID 수집
            points_to_delete = [
                result.id for result in search_result
                if result.score < similarity_threshold
            ]
            
            if points_to_delete:
                self.client.delete(
                    collection_name=collection_name,
                    points_selector=models.PointIdsList(
                        points=points_to_delete
                    )
                )
        except Exception as e:
            print(f"Error deleting embeddings by similarity: {e}")

    def cleanup_old_embeddings(self, session_id: int, days_threshold: int = 30) -> None:
        """특정 일수 이상 지난 임베딩들을 삭제합니다."""
        collection_name = f"session_{session_id}"
        try:
            from datetime import datetime, timedelta
            threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
            
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="created_at",
                                range=models.Range(
                                    lt=threshold_date.isoformat()
                                )
                            )
                        ]
                    )
                )
            )
        except Exception as e:
            print(f"Error cleaning up old embeddings: {e}")

    def search_similar(
        self,
        query: str,
        session_id: int, # This is the DB session.id (integer)
        limit: Optional[int] = 5,
        user_identifier: Optional[str] = None # New parameter for filtering
    ) -> List[Dict[str, Any]]:
        self._ensure_collection(session_id) # Collection name is based on DB session.id
        collection_name = f"session_{session_id}"
        
        query_embedding = self.get_embedding(query)
        search_limit = limit if limit is not None else 5

        query_filter = None
        if user_identifier:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(key='user_id', match=models.MatchValue(value=user_identifier))
                ]
            )
        
        search_result = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=query_filter, # Pass the filter
            limit=search_limit
        )
        
        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            }
            for result in search_result
        ]

    def delete_collection(self, collection_name: str) -> None:
        try:
            self.client.delete_collection(collection_name=collection_name)
            print(f"Collection {collection_name} deleted successfully")
        except Exception as e:
            print(f"Error deleting collection: {e}")

    def multi_stage_search(
        self,
        query: str,
        session_id: int,
        user_identifier: Optional[str] = None,
        limit_per_stage: int = 3,
        short_term_days_cutoff: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        self._ensure_collection(session_id)
        collection_name = f"session_{session_id}"
        query_embedding = self.get_embedding(query)

        base_filters = []
        if user_identifier:
            base_filters.append(models.FieldCondition(key='user_id', match=models.MatchValue(value=user_identifier)))

        all_results_map = {} # Using dict to store results by ID to handle potential duplicates by score

        # Stage 1: Short-term Search
        short_term_filters = list(base_filters)
        short_term_filters.append(models.FieldCondition(key='memory_type', match=models.MatchValue(value='short_term')))

        # timestamp field in VectorPayload needs to be used for date filtering.
        # Assuming 'timestamp' is stored as a datetime string or Unix timestamp compatible with Qdrant's range filters.
        # Qdrant expects ISO 8601 datetime strings for range filters on datetime fields if not using Unix timestamps.
        # Let's assume VectorPayload.timestamp is a datetime object, and we store its ISO format or Qdrant handles it.
        # For filtering, we need to ensure the payload's 'timestamp' field is correctly queryable.
        # The current VectorPayload model has `timestamp: datetime`. When this is converted to JSON for Qdrant,
        # it typically becomes an ISO string.
        if short_term_days_cutoff is not None:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=short_term_days_cutoff)
            # Assuming timestamp is stored in a way Qdrant can filter by range (e.g., ISO string or Unix timestamp)
            # If stored as ISO string:
            short_term_filters.append(models.FieldCondition(key='timestamp', range=models.Range(gte=cutoff_date.isoformat())))
            # If stored as Unix timestamp:
            # short_term_filters.append(models.FieldCondition(key='timestamp', range=models.Range(gte=int(cutoff_date.timestamp()))))
            # For now, assuming ISO format is implicitly handled by Qdrant/SQLModel during serialization to JSON.

        st_results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=models.Filter(must=short_term_filters) if short_term_filters else None,
            limit=limit_per_stage
        )
        for res in st_results:
            if res.id not in all_results_map or res.score > all_results_map[res.id].score:
                 all_results_map[res.id] = res

        # Stage 2: Summary Type Search
        summary_filters_list = list(base_filters)
        summary_filters_list.append(models.FieldCondition(key='memory_type', match=models.MatchValue(value='summary')))
        sum_results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=models.Filter(must=summary_filters_list) if summary_filters_list else None,
            limit=limit_per_stage
        )
        for res in sum_results:
            if res.id not in all_results_map or res.score > all_results_map[res.id].score:
                 all_results_map[res.id] = res

        # Stage 3: Long-term Search
        long_term_filters = list(base_filters)
        long_term_filters.append(models.FieldCondition(key='memory_type', match=models.MatchValue(value='long_term')))
        lt_results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=models.Filter(must=long_term_filters) if long_term_filters else None,
            limit=limit_per_stage
        )
        for res in lt_results:
            if res.id not in all_results_map or res.score > all_results_map[res.id].score:
                 all_results_map[res.id] = res

        # Convert map to list and sort by score
        combined_results_list = sorted(all_results_map.values(), key=lambda r: r.score, reverse=True)

        return [{"id": res.id, "score": res.score, "payload": res.payload} for res in combined_results_list]

class QdrantClientFactory:
    @staticmethod
    def create_client(
        url: Optional[str] = None,
        openai_client: Optional[openai.OpenAI] = None
    ) -> QdrantClientWrapper:
        """Qdrant 클라이언트를 생성합니다."""
        return QdrantClientWrapper(url=url or QDRANT_URL, openai_client=openai_client)

# FastAPI 의존성으로 제공
def get_qdrant_client() -> QdrantClientWrapper:
    """FastAPI 의존성 주입을 위한 Qdrant 클라이언트 생성 함수"""
    return QdrantClientFactory.create_client()


def insert_vector(
    client: QdrantClient,
    collection_name: str,
    vector: List[float],
    payload: VectorPayload,
    vector_id: Optional[int] = None,
) -> int:
    """Insert a vector with payload into the specified collection."""
    if vector_id is None:
        vector_id = int(datetime.utcnow().timestamp() * 1000)

    client.upsert(
        collection_name=collection_name,
        points=[
            models.PointStruct(id=vector_id, vector=vector, payload=payload.dict())
        ],
    )
    return vector_id


def search_vectors(
    client: QdrantClient,
    collection_name: str,
    query_vector: List[float],
    limit: int = 5,
    query_filter: Optional[models.Filter] = None,
) -> List[Dict[str, Any]]:
    """Search for similar vectors in a collection."""
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=limit,
    )
    return [
        {"id": r.id, "score": r.score, "payload": r.payload} for r in results
    ]
