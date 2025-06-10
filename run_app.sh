#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 환경 변수 파일 경로
ENV_FILE=".env"

# 필수 환경 변수 목록 (기본 환경 변수)
REQUIRED_ENV_VARS=(
    "VITE_API_URL"
    "VITE_API_VERSION"
    "VITE_FRONTEND_URL"
    "QDRANT_URL"
    "OPENAI_API_KEY"
    "OPENAI_ORGANIZATION_ID"
    "OPENAI_CHAT_MODEL"
    "OPENAI_EMBEDDING_MODEL"
    "DATABASE_URL"
)

# 환경 변수 파일이 존재하는지 확인
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo -e "${YELLOW}Please run setup_env.sh first to set up environment variables${NC}"
    exit 1
fi

# 환경 변수 파일 로드
echo "Loading environment variables from .env file..."
while IFS='=' read -r key value; do
    # 주석이나 빈 줄 무시
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z $key ]] && continue
    
    # 따옴표 제거
    value=$(echo "$value" | tr -d '"' | tr -d "'")
    
    # 환경 변수 설정
    export "$key=$value"
done < "$ENV_FILE"

# 기본 환경 변수 확인
echo "Checking basic environment variables..."
for var in "${REQUIRED_ENV_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: Required environment variable $var is not set${NC}"
        echo -e "${YELLOW}Please check your .env file and run setup_env.sh if needed${NC}"
        exit 1
    fi
done

# 환경 변수 출력
echo -e "${GREEN}All required environment variables are set!${NC}"
echo "Current environment variables:"
echo "VITE_API_URL: $VITE_API_URL"
echo "VITE_FRONTEND_URL: $VITE_FRONTEND_URL"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:10}..."
echo "DATABASE_URL: $DATABASE_URL"
echo "QDRANT_URL: $QDRANT_URL"
echo "OPENAI_CHAT_MODEL: $OPENAI_CHAT_MODEL"
echo "OPENAI_EMBEDDING_MODEL: $OPENAI_EMBEDDING_MODEL"
echo "VITE_API_VERSION: $VITE_API_VERSION"

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")"

# Qdrant 서버 상태 확인
echo "Checking Qdrant server status..."
if ! curl -s "${QDRANT_URL}/health" > /dev/null; then
    echo -e "${RED}Error: Qdrant server is not running${NC}"
    echo "Please start the Qdrant server first"
    exit 1
fi
echo -e "${GREEN}Qdrant server is running${NC}"

# 기존 서버 프로세스 종료
echo "Stopping existing server..."
API_PORT=$(echo ${VITE_API_URL} | sed -E 's/.*:([0-9]+).*/\1/')
if [ -z "$API_PORT" ]; then
    echo -e "${RED}Error: Could not extract port from VITE_API_URL${NC}"
    exit 1
fi

echo "Port ${API_PORT} is still in use. Killing the process..."
kill -9 $(lsof -t -i:${API_PORT})
# 프로세스가 완전히 종료될 때까지 대기
while lsof -i :${API_PORT} > /dev/null; do
    sleep 1
done
echo "Previous server process terminated."

# FastAPI 서버 시작
echo "Starting FastAPI server..."
nohup uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT} > nohup.out 2>&1 &

# 서버 시작 대기
echo "Waiting for server to start..."
for i in {1..30}; do
    if curl -s "${VITE_API_URL}/health" > /dev/null; then
        echo -e "${GREEN}Server started successfully.${NC}"
        echo -e "${GREEN}Server is running and ready. Check nohup.out for logs.${NC}"
        exit 0
    fi
    echo -n "."
    sleep 1
done

echo -e "${RED}Error: Server failed to start within 30 seconds${NC}"
echo "Checking server logs..."
cat nohup.out
exit 1 