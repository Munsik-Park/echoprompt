from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import session_router, query_router
from app.database import create_db_and_tables

app = FastAPI(
    title="EchoPrompt API",
    description="API for managing chat sessions and semantic search",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (prefix는 각 라우터 파일에서 지정)
app.include_router(session_router.router)
app.include_router(query_router.router)

@app.on_event("startup")
async def on_startup():
    """서버 시작 시 DB 테이블 생성"""
    create_db_and_tables()

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {"message": "Welcome to EchoPrompt API"} 