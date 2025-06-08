#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "Starting frontend tests..."

# 기존 테스트 결과 삭제
rm -rf "$FRONTEND_DIR/test-results"

# 기존 서버 프로세스 종료
pkill -f uvicorn
pkill -f vite

# 1. 백엔드 서버 재시작
echo -e "${GREEN}Restarting backend server...${NC}"
bash run_app.sh

# 2. 프론트엔드 서버 시작
echo -e "${GREEN}Starting frontend server...${NC}"
cd "$FRONTEND_DIR" && npm run dev &
FRONTEND_PID=$!

# 3. 서버 시작 대기
echo "Waiting for servers to start..."

# 백엔드 서버 상태 확인
echo "Checking backend server status..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null; then
        echo "Backend server is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Backend server failed to start"
        exit 1
    fi
    sleep 1
done

# 프론트엔드 서버 상태 확인
echo "Checking frontend server status..."
for i in {1..30}; do
    if curl -s http://localhost:3000/ > /dev/null; then
        echo "Frontend server is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Frontend server failed to start"
        exit 1
    fi
    sleep 1
done

# 추가 대기 시간 (서버가 완전히 준비되도록)
sleep 2

# 4. Playwright 테스트 실행
echo -e "${GREEN}Running Playwright tests...${NC}"
cd "$FRONTEND_DIR" && npx playwright test

# 5. 테스트 결과 저장
TEST_RESULT=$?

# 6. 프론트엔드 서버 종료
echo -e "${GREEN}Cleaning up...${NC}"
kill $FRONTEND_PID

# Cleanup
echo -e "${GREEN}Cleaning up...${NC}"
pkill -f uvicorn
pkill -f vite
pkill -f playwright
pkill -f chromium
pkill -f firefox
pkill -f webkit

# 7. 테스트 결과에 따라 종료
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}Tests completed successfully!${NC}"
    exit 0
else
    echo -e "${RED}Tests failed. Check the test report for details.${NC}"
    exit 1
fi 