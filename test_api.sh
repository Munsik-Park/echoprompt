#!/bin/bash
set -e

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")"

# 환경 변수 로드
source reset_env.sh

if [ -z "$VITE_API_URL" ]; then
    echo "Error: VITE_API_URL environment variable is not set"
    exit 1
fi

if [ -z "$VITE_API_VERSION" ]; then
    echo "Error: VITE_API_VERSION environment variable is not set"
    exit 1
fi

# API URL 구성
BASE_URL="$VITE_API_URL"
API_URL="$VITE_API_URL/api/$VITE_API_VERSION"

# 서버 상태 확인 함수
check_server() {
    local max_attempts=3
    local attempt=1
    local wait_time=2

    echo "서버 상태 확인 중..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$BASE_URL/docs" > /dev/null; then
            echo "✅ 서버가 정상적으로 실행 중입니다."
            return 0
        fi
        echo "서버 시작 대기 중... (시도 $attempt/$max_attempts)"
        sleep $wait_time
        attempt=$((attempt + 1))
    done
    
    echo "❌ 서버가 응답하지 않습니다."
    return 1
}

# 서버 상태 확인
if ! check_server; then
    echo "서버를 시작해주세요."
    exit 1
fi

echo "=== 0. Swagger 문서 검증 ==="
echo "1. Swagger UI 접근 확인"
if curl -s -f "$BASE_URL/docs" > /dev/null; then
    echo "✅ Swagger UI 접근 성공"
else
    echo "❌ Swagger UI 접근 실패"
    exit 1
fi

echo -e "\n2. OpenAPI Spec 다운로드"
if curl -s -f -o openapi.json "$BASE_URL/openapi.json"; then
    echo "✅ OpenAPI Spec 다운로드 성공"
    # OpenAPI Spec에서 엔드포인트 목록 추출
    echo -e "\n3. API 엔드포인트 목록:"
    grep -o '"path":"[^"]*"' openapi.json | sed 's/"path":"//g' | sed 's/"//g'
else
    echo "❌ OpenAPI Spec 다운로드 실패"
    exit 1
fi

echo "=== 1. 세션 생성 ==="
SESSION_ID=$(curl -s -X POST "$API_URL/sessions" -H "Content-Type: application/json" -d '{"name": "테스트 세션"}' | jq .id)
echo "[TEST] Created session: $SESSION_ID"
if [ -z "$SESSION_ID" ] || [ "$SESSION_ID" = "null" ]; then
  echo "[ERROR] 세션 생성 실패"
  exit 1
fi

echo -e "\n=== 2. 세션에 메시지 추가 ==="
MESSAGE_RES=$(curl -s -X POST "$API_URL/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"content": "테스트 메시지", "role": "user"}')
echo "[TEST] Message add response: $MESSAGE_RES"
MESSAGE_ID=$(echo $MESSAGE_RES | jq .id)
if [ -z "$MESSAGE_ID" ] || [ "$MESSAGE_ID" = "null" ]; then
  echo "[ERROR] 메시지 추가 실패"
  exit 1
fi

echo -e "\n=== 3. 세션 메시지 조회 ==="
MESSAGES_RESPONSE=$(curl -s -X GET "$API_URL/sessions/$SESSION_ID/messages")
echo "응답: $MESSAGES_RESPONSE"

echo -e "\n=== 4. 의미 기반 검색 ==="
SEARCH_RES=$(curl -s -X POST "$API_URL/query/semantic_search" -H "Content-Type: application/json" -d "{\"query\": \"테스트\", \"session_id\": $SESSION_ID, \"limit\": 5}")
echo "[TEST] Semantic search response: $SEARCH_RES"
SEARCH_COUNT=$(echo $SEARCH_RES | jq '.results | length')
if [ "$SEARCH_COUNT" -eq 0 ]; then
  echo "[ERROR] 의미 기반 검색 실패"
  exit 1
fi

echo -e "\n=== 5. 세션 정보 업데이트 ==="
UPDATE_SESSION_RESPONSE=$(curl -s -X PUT "$API_URL/sessions/$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"name": "업데이트된 테스트 세션"}')
echo "응답: $UPDATE_SESSION_RESPONSE"

echo -e "\n=== 6. 메시지 업데이트 ==="
UPDATE_MESSAGE_RESPONSE=$(curl -s -X PUT "$API_URL/sessions/$SESSION_ID/messages/$MESSAGE_ID" \
  -H "Content-Type: application/json" \
  -d '{"content": "업데이트된 메시지입니다!", "role": "user"}')
echo "응답: $UPDATE_MESSAGE_RESPONSE"

echo -e "\n=== 7. 메시지 삭제 ==="
DELETE_MESSAGE_RESPONSE=$(curl -s -X DELETE "$API_URL/sessions/$SESSION_ID/messages/$MESSAGE_ID")
echo "응답 상태 코드: $?"

echo -e "\n=== 8. 세션 삭제 ==="
DELETE_SESSION_RESPONSE=$(curl -s -X DELETE "$API_URL/sessions/$SESSION_ID")
echo "응답 상태 코드: $?"

# OpenAPI Spec 정리
rm -f openapi.json

echo "[SUCCESS] 모든 API 테스트가 정상적으로 완료되었습니다." 