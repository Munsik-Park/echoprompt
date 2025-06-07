import os
from typing import List, Tuple, Optional
from qdrant_client import QdrantClient as QdrantClientBase
from qdrant_client.http import models
from dotenv import load_dotenv
import requests
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

# .env 파일 로드
load_dotenv()

# 환경 변수 설정
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORGANIZATION_ID")
COLLECTION_NAME = "echoprompt_messages"

# OpenAI API 설정
OPENAI_API_URL = "https://api.openai.com/v1/embeddings"
OPENAI_MODEL = "text-embedding-ada-002"

class QdrantClient:
    def __init__(self):
        self.client = QdrantClientBase(
            host=QDRANT_URL.replace("http://", "").split(":")[0],
            port=int(QDRANT_URL.split(":")[-1]),
            api_key=QDRANT_API_KEY if QDRANT_API_KEY else None
        )
        self.collection_name = "messages"
        self._ensure_collection()

    def _ensure_collection(self):
        """컬렉션이 없으면 생성합니다."""
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1536,  # OpenAI ada-002 모델의 임베딩 크기
                    distance=models.Distance.COSINE
                )
            )

    def get_embedding(self, text: str) -> list:
        """텍스트의 임베딩을 생성합니다."""
        # TODO: 실제 임베딩 생성 로직 구현
        return [0.0] * 1536  # 임시로 0으로 채운 벡터 반환

    def store_embedding(
        self,
        message_id: int,
        session_id: int,
        content: str,
        embedding: list
    ):
        """메시지의 임베딩을 저장합니다."""
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=message_id,
                    vector=embedding,
                    payload={
                        "session_id": session_id,
                        "content": content
                    }
                )
            ]
        )

    def search_similar(
        self,
        query_embedding: list,
        session_id: int,
        limit: int = 5
    ) -> list:
        """주어진 임베딩과 유사한 메시지를 검색합니다."""
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="session_id",
                        match=models.MatchValue(value=session_id)
                    )
                ]
            ),
            limit=limit
        )
        return search_result

# QdrantClient 인스턴스 생성 및 export
qdrant_client = QdrantClient()

class QdrantWrapper:
    def __init__(self):
        """Qdrant 클라이언트 초기화"""
        self.client = QdrantClientBase(url=QDRANT_URL)
        self._ensure_collection()

    def _ensure_collection(self):
        """컬렉션이 존재하는지 확인하고 없으면 생성"""
        collections = self.client.get_collections().collections
        if not any(c.name == COLLECTION_NAME for c in collections):
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=1536,  # OpenAI ada-002 임베딩 크기
                    distance=models.Distance.COSINE
                )
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_embedding(self, text: str) -> List[float]:
        """텍스트의 임베딩 벡터 생성 (재시도 로직 포함)"""
        try:
            # API 요청 헤더 설정
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            if OPENAI_ORG_ID:
                headers["OpenAI-Organization"] = OPENAI_ORG_ID

            # API 요청 데이터
            data = {
                "input": text,
                "model": OPENAI_MODEL
            }

            # API 호출
            response = requests.post(
                OPENAI_API_URL,
                headers=headers,
                json=data,
                timeout=30  # 30초 타임아웃 설정
            )
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

            # 응답에서 임베딩 추출
            result = response.json()
            return result["data"][0]["embedding"]

        except requests.exceptions.Timeout:
            print("OpenAI API 요청 시간 초과")
            raise
        except requests.exceptions.RequestException as e:
            print(f"OpenAI API 요청 중 오류 발생: {str(e)}")
            raise
        except Exception as e:
            print(f"임베딩 생성 중 오류 발생: {str(e)}")
            raise

    async def store_message_embedding(
        self,
        message_id: str,
        session_id: int,
        content: str
    ) -> None:
        """메시지 임베딩을 생성하고 Qdrant에 저장"""
        try:
            # 텍스트 임베딩 생성
            embedding = await self.get_embedding(content)
            
            # Qdrant에 저장
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=message_id,
                        vector=embedding,
                        payload={
                            "session_id": session_id,
                            "content": content
                        }
                    )
                ]
            )
        except Exception as e:
            print(f"임베딩 저장 중 오류 발생: {str(e)}")
            raise

    async def search_similar_messages(
        self,
        query: str,
        session_id: int,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """유사한 메시지 검색"""
        try:
            # 쿼리 임베딩 생성
            query_embedding = await self.get_embedding(query)
            
            # Qdrant에서 검색
            search_result = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="session_id",
                            match=models.MatchValue(value=session_id)
                        )
                    ]
                ),
                limit=top_k
            )
            return [(hit.id, hit.score) for hit in search_result]
        except Exception as e:
            print(f"메시지 검색 중 오류 발생: {str(e)}")
            raise

# Qdrant 클라이언트 인스턴스 생성
qdrant = QdrantWrapper() 