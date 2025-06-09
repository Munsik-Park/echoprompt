import os
from typing import List, Tuple, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv
import requests
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
import openai
from app.openai_client import OpenAIClientFactory

# .env 파일 로드
load_dotenv()

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
    def __init__(self, url: Optional[str] = None, openai_client: Optional[openai.OpenAI] = None):
        self.client = QdrantClient(url=url or QDRANT_URL)
        self.openai_client = openai_client or OpenAIClientFactory.create_client()
        self.collection_name = "messages"
        self._ensure_collection()

    def _ensure_collection(self, session_id: Optional[int] = None):
        """세션 ID 기반으로 컬렉션을 생성하거나 확인합니다."""
        if session_id is None:
            collection_name = self.collection_name
        else:
            collection_name = f"session_{session_id}"
            
        try:
            collections = self.client.get_collections().collections
            if not any(c.name == collection_name for c in collections):
                print(f"Creating collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=1536,  # OpenAI ada-002 embedding size
                        distance=models.Distance.COSINE
                    )
                )
                print(f"Collection {collection_name} created successfully")
        except Exception as e:
            print(f"Error ensuring collection {collection_name}: {str(e)}")
            raise

    def get_embedding(self, text: str) -> list:
        """텍스트의 임베딩 벡터 생성"""
        try:
            # 텍스트가 문자열인지 확인하고 필요시 인코딩 처리
            if not isinstance(text, str):
                text = str(text)
            
            # 텍스트를 UTF-8로 인코딩
            text = text.encode('utf-8').decode('utf-8')
            
            # OpenAI 클라이언트 사용
            response = self.openai_client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
            
        except Exception as e:
            print(f"임베딩 생성 중 오류 발생: {str(e)}")
            raise

    def store_embedding(self, message_id: int, session_id: int, content: str, embedding: list):
        """메시지 임베딩을 저장합니다."""
        if session_id is None:
            raise ValueError("session_id must be provided")
            
        try:
            collection_name = f"session_{session_id}"
            # 컬렉션 존재 확인 및 생성
            self._ensure_collection(session_id)
            
            # 임베딩 저장
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=message_id,
                        vector=embedding,
                        payload={
                            "content": content,
                            "session_id": session_id,
                            "role": "user"  # 기본값으로 user 설정
                        }
                    )
                ]
            )
            print(f"Embedding stored successfully in collection {collection_name}")
        except Exception as e:
            print(f"Error storing embedding: {str(e)}")
            raise

    def search_similar(self, query: str, session_id: int, limit: int = 10) -> List[dict]:
        """주어진 쿼리와 유사한 메시지를 검색합니다."""
        try:
            # 컬렉션 이름 생성
            collection_name = f"session_{session_id}"
            
            # 컬렉션이 존재하는지 확인
            collections = self.client.get_collections().collections
            if not any(c.name == collection_name for c in collections):
                return []

            # 쿼리 임베딩 생성
            response = self.openai_client.embeddings.create(
                input=query,
                model="text-embedding-ada-002"
            )
            query_embedding = response.data[0].embedding

            # 검색 수행
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit
            )

            # 결과 변환
            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "content": result.payload.get("content", ""),
                    "role": result.payload.get("role", "user")
                }
                for result in search_results
            ]
        except Exception as e:
            print(f"Error in search_similar: {str(e)}")
            raise

    def delete_embedding(self, message_id: int, session_id: int) -> None:
        """특정 메시지의 임베딩을 삭제합니다."""
        try:
            collection_name = f"session_{session_id}"
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=[message_id]),
            )
        except Exception as e:
            print(f"Error deleting embedding: {str(e)}")
            raise

    def delete_session_embeddings(self, session_id: int) -> None:
        """세션의 모든 임베딩을 삭제합니다."""
        try:
            collection_name = f"session_{session_id}"
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="session_id",
                                match=models.MatchValue(value=session_id),
                            )
                        ]
                    )
                ),
            )
        except Exception as e:
            print(f"Error deleting session embeddings: {str(e)}")
            raise

class QdrantClientFactory:
    @staticmethod
    def create_client(
        url: Optional[str] = None,
        openai_client: Optional[openai.OpenAI] = None
    ) -> QdrantClientWrapper:
        """Qdrant 클라이언트를 생성합니다."""
        return QdrantClientWrapper(url=url, openai_client=openai_client)

# FastAPI 의존성으로 제공
def get_qdrant_client() -> QdrantClientWrapper:
    """FastAPI 의존성 주입을 위한 Qdrant 클라이언트 생성 함수"""
    return QdrantClientFactory.create_client() 