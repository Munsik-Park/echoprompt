#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 필수 환경 변수 목록
REQUIRED_ENV_VARS=(
    "VITE_API_URL"
    "VITE_API_VERSION"
    "VITE_FRONTEND_URL"
)

# .env 파일 존재 확인
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# .env 파일에서 환경 변수 로드
echo "Loading environment variables from .env file..."
while IFS='=' read -r key value; do
    # 주석이나 빈 줄 무시
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z $key ]] && continue
    
    # 따옴표 제거
    value=$(echo "$value" | tr -d '"' | tr -d "'")
    
    # 환경 변수 설정
    export "$key=$value"
done < .env

# 필수 환경 변수 확인
echo "Checking required environment variables..."
for var in "${REQUIRED_ENV_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: Required environment variable $var is not set${NC}"
        exit 1
    fi
done

# 현재 환경 변수 값 출력
echo -e "\nCurrent environment variables:"
echo -e "${GREEN}VITE_API_URL: ${VITE_API_URL}${NC}"
echo -e "${GREEN}VITE_FRONTEND_URL: ${VITE_FRONTEND_URL}${NC}"

# Frontend 서버 포트 추출
FRONTEND_PORT=$(echo ${VITE_FRONTEND_URL} | sed -E 's/.*:([0-9]+).*/\1/')
if [ -z "$FRONTEND_PORT" ]; then
    echo -e "${RED}Error: Could not extract port from VITE_FRONTEND_URL${NC}"
    exit 1
fi

# 기존 서버 프로세스 종료
echo -e "\nStopping existing server processes..."
lsof -ti:${FRONTEND_PORT} | xargs kill -9 2>/dev/null || true

# 프론트엔드 서버 시작
echo -e "\nStarting frontend server..."
cd frontend
npm run dev -- --host 0.0.0.0 --port ${FRONTEND_PORT} &

# 서버 시작 대기
echo "Waiting for server to start..."
for i in {1..30}; do
    if curl -s "${VITE_FRONTEND_URL}" > /dev/null; then
        echo -e "${GREEN}Server started successfully${NC}"
        exit 0
    fi
    echo -n "."
    sleep 1
done

echo -e "${RED}Error: Server failed to start${NC}"
exit 1 