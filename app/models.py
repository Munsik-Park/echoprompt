from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField

# SQLModel 기반 데이터베이스 모델
class SessionBase(SQLModel):
    name: str = Field(..., description="세션 이름")

class Session(SessionBase, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)

class MessageBase(SQLModel):
    content: str = Field(..., description="메시지 내용")
    role: str = Field(..., description="메시지 발신자 역할 (user/assistant)")

class Message(MessageBase, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    session_id: int = SQLField(foreign_key="session.id")
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    embedding_id: Optional[str] = SQLField(default=None)

# Pydantic 기반 API 요청/응답 모델
class SessionCreate(SessionBase):
    pass

class SessionUpdate(SessionBase):
    name: Optional[str] = Field(None, description="업데이트할 세션 이름")

class SessionResponse(SessionBase):
    id: int
    created_at: datetime
    updated_at: datetime

class MessageCreate(MessageBase):
    pass

class MessageUpdate(MessageBase):
    content: Optional[str] = Field(None, description="업데이트할 메시지 내용")
    role: Optional[str] = Field(None, description="업데이트할 메시지 역할")

class MessageResponse(MessageBase):
    id: int
    session_id: int
    created_at: datetime
    embedding_id: Optional[str]

class QueryRequest(BaseModel):
    query: str = Field(..., description="검색 쿼리")
    session_id: int = Field(..., description="세션 ID")
    top_k: int = Field(default=5, description="반환할 결과 수")

class QueryResponse(BaseModel):
    messages: List[MessageResponse]
    similarity_scores: List[float]

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="의미론적 검색 쿼리")
    session_id: int = Field(..., description="세션 ID")
    top_k: int = Field(default=5, description="반환할 결과 수")
    similarity_threshold: float = Field(default=0.7, description="유사도 임계값")

class SemanticSearchResponse(BaseModel):
    messages: List[MessageResponse]
    similarity_scores: List[float]
    total_matches: int 