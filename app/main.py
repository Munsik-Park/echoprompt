from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import session_router, query_router, chat_router, user_router, collection_router # Added new routers
from app.database import create_db_and_tables
# Ensure all models are imported so SQLModel.metadata knows about them
from app.models import UserModel, CollectionModel, CollectionUserLinkModel # Added to ensure tables are created
from app.config import settings
import os
import logging

# 필수 환경 변수 확인
if not os.getenv('VITE_FRONTEND_PORT'):
    raise ValueError("VITE_FRONTEND_PORT environment variable is not set")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI(
    title="EchoPrompt API",
    description="EchoPrompt Backend API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        f"http://localhost:{os.getenv('VITE_FRONTEND_PORT')}",
        f"http://127.0.0.1:{os.getenv('VITE_FRONTEND_PORT')}"
    ],  # 프론트엔드 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(session_router.router)
app.include_router(query_router.router)
app.include_router(chat_router.router)
app.include_router(user_router.router) # Added new router
app.include_router(collection_router.router) # Added new router

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
