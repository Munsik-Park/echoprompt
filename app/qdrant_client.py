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
        embedding: List[float]
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
                        "session_id": session_id
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

    def search_similar(
        self,
        query: str,
        session_id: int,
        limit: Optional[int] = 5
    ) -> List[Dict[str, Any]]:
        self._ensure_collection(session_id)
        collection_name = f"session_{session_id}"
        
        query_embedding = self.get_embedding(query)
        
        # limit이 None이면 기본값 5 사용
        search_limit = limit if limit is not None else 5
        
        search_result = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
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
