import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Frontend Configuration
    VITE_FRONTEND_HOST: str
    VITE_FRONTEND_PORT: Optional[int] = None
    
    # API Configuration
    VITE_API_HOST: str
    VITE_API_PORT: Optional[int] = None
    VITE_API_VERSION: str = "v1"
    
    # Qdrant Configuration
    QDRANT_HOST: str
    QDRANT_PORT: Optional[int] = None
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_ORGANIZATION_ID: Optional[str] = None
    OPENAI_CHAT_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Database Configuration
    DATABASE_HOST: str
    DATABASE_PORT: Optional[int] = None
    DATABASE_NAME: Optional[str] = None

    @property
    def API_PREFIX(self) -> str:
        return f"/api/{self.VITE_API_VERSION}"

    @property
    def API_URL(self) -> str:
        if self.VITE_API_PORT:
            return f"http://{self.VITE_API_HOST}:{self.VITE_API_PORT}"
        return f"http://{self.VITE_API_HOST}"

    @property
    def FRONTEND_URL(self) -> str:
        if self.VITE_FRONTEND_PORT:
            return f"http://{self.VITE_FRONTEND_HOST}:{self.VITE_FRONTEND_PORT}"
        return f"http://{self.VITE_FRONTEND_HOST}"

    @property
    def QDRANT_URL(self) -> str:
        if self.QDRANT_PORT:
            return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"
        return f"http://{self.QDRANT_HOST}"

    @property
    def DATABASE_URL(self) -> str:
        # SQLite URL 형식인 경우 그대로 반환
        if self.DATABASE_HOST.startswith('sqlite:///'):
            return self.DATABASE_HOST
        # PostgreSQL URL 형식인 경우
        if not self.DATABASE_NAME:
            raise ValueError("DATABASE_NAME is required for PostgreSQL")
        if self.DATABASE_PORT:
            return f"postgresql://{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        return f"postgresql://{self.DATABASE_HOST}/{self.DATABASE_NAME}"

    class Config:
        env_file = None  # .env 파일 직접 접근 제거
        env_file_encoding = 'utf-8'

settings = Settings() 