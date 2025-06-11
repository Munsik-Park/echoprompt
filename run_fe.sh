#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")"

# 가상 환경 확인 함수
check_venv() {
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "✅ 가상 환경이 활성화되어 있습니다: $VIRTUAL_ENV"
        return 0
    else
        echo "❌ 가상 환경이 활성화되어 있지 않습니다"
        echo "다음 명령어로 가상 환경을 활성화하세요:"
        echo "source venv/bin/activate"
        return 1
    fi
}

# 스크립트 시작 시 가상 환경 확인
if ! check_venv; then
    exit 1
fi

# 필수 환경 변수 목록
REQUIRED_ENV_VARS=(
    "VITE_API_URL"
    "VITE_API_VERSION"
    "VITE_FRONTEND_URL"
)

# 환경 변수 초기화
source reset_env.sh

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