import os
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수에서 데이터베이스 URL 가져오기
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./echoprompt.db")

# SQLAlchemy 기본 설정
Base = declarative_base()

class DatabaseFactory:
    """데이터베이스 엔진과 세션을 생성하는 팩토리 클래스"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(
            self.database_url,
            connect_args={"check_same_thread": False} if self.database_url.startswith("sqlite") else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """데이터베이스 테이블 생성"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Generator[Session, None, None]:
        """데이터베이스 세션 생성"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

# 기본 데이터베이스 팩토리 인스턴스
db_factory = DatabaseFactory()

# FastAPI 의존성으로 제공
def get_db() -> Generator[Session, None, None]:
    """FastAPI 의존성 주입을 위한 데이터베이스 세션 생성 함수"""
    db = db_factory.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 이전 코드와의 호환성을 위한 함수
def create_db_and_tables():
    """데이터베이스 테이블을 생성합니다."""
    db_factory.create_tables() 