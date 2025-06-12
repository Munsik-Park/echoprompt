import openai
from openai import OpenAI
import os
from typing import Optional
from dotenv import load_dotenv
import logging

# .env 파일 로드
load_dotenv()

logger = logging.getLogger("openai_client")

def get_openai_client() -> OpenAI:
    """FastAPI 의존성 주입을 위한 OpenAI 클라이언트 생성 함수"""
    api_key = os.getenv("OPENAI_API_KEY")
    organization_id = os.getenv("OPENAI_ORGANIZATION_ID")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    if not organization_id:
        raise ValueError("OPENAI_ORGANIZATION_ID environment variable is not set")
    
    # 프록시 설정이 필요한 경우 환경 변수를 통해 설정
    # os.environ["HTTP_PROXY"] = "http://your.proxy.server"
    # os.environ["HTTPS_PROXY"] = "http://your.proxy.server"
    
    try:
        client = OpenAI(
            api_key=api_key,
            organization=organization_id,
            base_url="https://api.openai.com/v1"
        )
        logger.info("OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"OpenAI client initialization failed: {e}")
        raise
    
    return client 