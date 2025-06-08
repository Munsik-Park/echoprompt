#!/bin/bash
# venv 활성화
source venv/bin/activate

# 환경 변수 초기화 및 새로 로드
echo "Initializing environment variables..."
unset OPENAI_API_KEY
unset OPENAI_ORGANIZATION_ID
unset QDRANT_URL
unset DATABASE_URL

# .env 파일에서 환경 변수 로드
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found!"
    exit 1
fi

# Qdrant 서버 상태 확인
echo "Checking Qdrant server status..."
if ! curl -s http://localhost:6333/healthz > /dev/null; then
    echo "Starting Qdrant server..."
    docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
    sleep 5  # Qdrant 서버 시작 대기
fi
echo "Qdrant server is running."

# DB 초기화 (필요시)
python -c "from app.database import create_db_and_tables; create_db_and_tables()"

# 기존 서버 종료
echo "Stopping existing server..."
# 메인 uvicorn 프로세스 종료
pkill -9 -f "uvicorn app.main:app"
# 파일 감시 프로세스 종료
pkill -9 -f "multiprocessing.spawn"
pkill -9 -f "multiprocessing.resource_tracker"
sleep 3  # 프로세스 종료 대기

# 포트 사용 확인 및 강제 종료
if lsof -i :8000 > /dev/null; then
    echo "Port 8000 is still in use. Killing the process..."
    PID=$(lsof -ti :8000)
    kill -9 $PID
    sleep 2
    if lsof -i :8000 > /dev/null; then
        echo "Error: Port 8000 is still in use after kill. Please check manually."
        exit 1
    fi
fi

# 새 서버 시작
echo "Starting FastAPI server..."
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > nohup.out 2>&1 &
echo "Server started. Check nohup.out for logs." 