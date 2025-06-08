import os
from typing import Generator
from sqlmodel import SQLModel, Session, create_engine
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 데이터베이스 URL 설정
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./echoprompt.db")

# SQLite 엔진 생성
engine = create_engine(DATABASE_URL, echo=True, future=True)

def get_session() -> Generator[Session, None, None]:
    """데이터베이스 세션을 생성하고 반환합니다."""
    with Session(engine, expire_on_commit=False) as session:
        yield session

def get_db() -> Generator[Session, None, None]:
    """FastAPI 의존성 주입을 위한 데이터베이스 세션 생성 함수"""
    with Session(engine, expire_on_commit=False) as session:
        yield session

def create_db_and_tables():
    """데이터베이스 테이블을 생성합니다."""
    SQLModel.metadata.create_all(engine) 