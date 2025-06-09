from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import session_router, query_router, chat_router
from app.database import create_db_and_tables

app = FastAPI(
    title="EchoPrompt API",
    description="EchoPrompt Backend API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 프론트엔드 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(session_router.router)
app.include_router(query_router.router)
app.include_router(chat_router.router)

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 DB 테이블 생성"""
    create_db_and_tables()

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

@app.get(
    "/",
    tags=["Root"],
    summary="API root",
    description="Health check endpoint",
)
async def root():
    """Root endpoint returning a welcome message."""
    return {"message": "Welcome to EchoPrompt API"}
