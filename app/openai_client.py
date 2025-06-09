import openai
import os
from typing import Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class OpenAIClientFactory:
    @staticmethod
    def create_client(
        api_key: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> openai.OpenAI:
        """OpenAI 클라이언트를 생성합니다."""
        return openai.OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            organization=organization_id or os.getenv("OPENAI_ORGANIZATION_ID")
        )

# FastAPI 의존성으로 제공
def get_openai_client() -> openai.OpenAI:
    """FastAPI 의존성 주입을 위한 OpenAI 클라이언트 생성 함수"""
    return OpenAIClientFactory.create_client() 