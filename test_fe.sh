#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")"

# 환경 변수 로드
source reset_env.sh

# 필수 환경 변수 확인
if [ -z "$VITE_API_URL" ]; then
    echo -e "${RED}Error: VITE_API_URL environment variable is not set${NC}"
    exit 1
fi

if [ -z "$VITE_FRONTEND_URL" ]; then
    echo -e "${RED}Error: VITE_FRONTEND_URL environment variable is not set${NC}"
    exit 1
fi

# API 서버 상태 확인
echo "Checking API server status..."
if ! curl -s "${VITE_API_URL}/api/v1/health" > /dev/null; then
    echo -e "${RED}Error: API server is not running at ${VITE_API_URL}${NC}"
    echo -e "${YELLOW}Please start the API server first:${NC}"
    echo -e "  ./run_app.sh"
    exit 1
fi
echo -e "${GREEN}API server is running${NC}"

# 프론트엔드 서버 상태 확인
echo "Checking frontend server status..."
if ! curl -s "${VITE_FRONTEND_URL}" > /dev/null; then
    echo -e "${RED}Error: Frontend server is not running at ${VITE_FRONTEND_URL}${NC}"
    echo -e "${YELLOW}Please start the frontend server first:${NC}"
    echo -e "  ./run_fe.sh"
    exit 1
fi
echo -e "${GREEN}Frontend server is running${NC}"

# 테스트 실행 전 세션 정리
echo "Cleaning up sessions before running tests..."
bash cleanup_sessions.sh
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Sessions cleaned up successfully.${NC}"
else
    echo -e "${RED}Warning: Failed to clean up sessions.${NC}"
    echo -e "${YELLOW}Continuing with tests anyway...${NC}"
fi

# Playwright 실행
echo "Running Playwright tests..."
cd frontend

# Playwright 실행 전에 환경 변수 설정
export PLAYWRIGHT_BASE_URL="${VITE_FRONTEND_URL}"
export PLAYWRIGHT_API_URL="${VITE_API_URL}"

# Playwright 실행
npx playwright test

# 테스트 결과 확인
if [ $? -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi

# 서버 상태 재확인
echo "Verifying server status after tests..."

# API 서버 상태 확인
if curl -s "${VITE_API_URL}/api/v1/health" > /dev/null; then
    echo -e "${GREEN}API server is still running${NC}"
else
    echo -e "${RED}Error: API server is not responding${NC}"
    exit 1
fi

# 프론트엔드 서버 상태 확인
if curl -s "${VITE_FRONTEND_URL}" > /dev/null; then
    echo -e "${GREEN}Frontend server is still running${NC}"
else
    echo -e "${RED}Error: Frontend server is not responding${NC}"
    exit 1
fi 