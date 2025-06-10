import openai
import os
from typing import Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def get_openai_client() -> openai.OpenAI:
    """FastAPI 의존성 주입을 위한 OpenAI 클라이언트 생성 함수"""
    api_key = os.getenv("OPENAI_API_KEY")
    organization_id = os.getenv("OPENAI_ORGANIZATION_ID")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    client = openai.OpenAI(
        api_key=api_key,
        organization=organization_id
    )
    
    return client 