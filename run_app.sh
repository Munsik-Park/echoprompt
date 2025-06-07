#!/bin/bash
# venv 활성화
source venv/bin/activate

# Qdrant 서버 상태 확인
echo "Checking Qdrant server status..."
if ! curl -s http://localhost:6333/healthz > /dev/null; then
    echo "Error: Qdrant server is not running!"
    echo "Please start Qdrant server first:"
    echo "1. Using Docker: docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant"
    echo "2. Or using Homebrew: brew install qdrant && qdrant"
    exit 1
fi
echo "Qdrant server is running."

# DB 초기화 (필요시)
python -c "from app.database import create_db_and_tables; create_db_and_tables()"

# 기존 서버 종료
echo "Stopping existing server..."
pkill -9 -f uvicorn

# FastAPI 서버 실행
echo "Starting FastAPI server..."
nohup uvicorn app.main:app --reload > nohup.out 2>&1 &
echo "Server started. Check nohup.out for logs." 