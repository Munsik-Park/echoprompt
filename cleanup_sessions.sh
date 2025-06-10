#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 환경 변수 체크
if [ -z "$VITE_API_URL" ]; then
    echo -e "${RED}Error: VITE_API_URL environment variable is not set${NC}"
    exit 1
fi

if [ -z "$VITE_API_VERSION" ]; then
    echo -e "${RED}Error: VITE_API_VERSION environment variable is not set${NC}"
    exit 1
fi

echo "테스트 세션 정리 중..."

# API URL 설정
API_URL="${VITE_API_URL}/api/${VITE_API_VERSION}"

# jq 설치 확인
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is not installed. Please install it first.${NC}"
    echo "You can install it using: brew install jq"
    exit 1
fi

# 모든 세션 조회
echo "세션 목록 조회 중..."
RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/sessions")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
SESSIONS=$(echo "$RESPONSE" | sed '$d')

# HTTP 상태 코드 확인
if [ "$HTTP_CODE" -eq 404 ]; then
    echo -e "${YELLOW}세션이 없습니다.${NC}"
    exit 0
elif [ "$HTTP_CODE" -ne 200 ]; then
    echo -e "${RED}세션 목록 조회 실패: HTTP ${HTTP_CODE}${NC}"
    echo "Response: $SESSIONS"
    exit 1
fi

# JSON 응답이 유효한지 확인
if ! echo "$SESSIONS" | jq empty 2>/dev/null; then
    echo -e "${RED}잘못된 JSON 응답: ${SESSIONS}${NC}"
    exit 1
fi

# 세션 목록이 비어있는지 확인
if [ "$(echo "$SESSIONS" | jq 'length')" -eq 0 ]; then
    echo -e "${YELLOW}세션이 없습니다.${NC}"
    exit 0
fi

# 각 세션 삭제
echo "$SESSIONS" | jq -c '.[]' | while read -r session; do
    SESSION_ID=$(echo "$session" | jq -r '.id')
    SESSION_NAME=$(echo "$session" | jq -r '.name')
    
    echo -e "${YELLOW}세션 삭제 중: ${SESSION_NAME} (ID: ${SESSION_ID})${NC}"
    
    # 세션 삭제 (HTTP 상태 코드 확인)
    RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE "${API_URL}/sessions/${SESSION_ID}")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 204 ]; then
        echo -e "${GREEN}세션 삭제 완료: ${SESSION_NAME} (ID: ${SESSION_ID})${NC}"
    else
        echo -e "${RED}세션 삭제 실패: ${SESSION_NAME} (ID: ${SESSION_ID}) - HTTP ${HTTP_CODE}${NC}"
        echo "Response: $RESPONSE_BODY"
    fi
done

echo -e "${GREEN}모든 테스트 세션이 정리되었습니다.${NC}" 