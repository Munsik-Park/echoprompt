#!/bin/bash
set -e

# 공통 함수 로드
source "$(dirname "$0")/utils.sh"

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")"

# 가상 환경 확인
if ! check_venv; then
    exit 1
fi

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

# API 문서 디렉토리 설정
API_DOCS_DIR="frontend/tests/api"
mkdir -p "$API_DOCS_DIR"

# 서버 상태 확인
if ! check_server "$BASE_URL/docs"; then
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
if curl -s -f -o "$API_DOCS_DIR/openapi.json" "$BASE_URL/openapi.json"; then
    echo "✅ OpenAPI Spec 다운로드 성공"
    # OpenAPI Spec에서 엔드포인트 목록 추출
    echo -e "\n3. API 엔드포인트 목록:"
    grep -o '"path":"[^"]*"' "$API_DOCS_DIR/openapi.json" | sed 's/"path":"//g' | sed 's/"//g'
else
    echo "❌ OpenAPI Spec 다운로드 실패"
    exit 1
fi

echo -e "\n=== 1. API 루트 확인 ==="
ROOT_RESPONSE=$(curl -s -X GET "$BASE_URL")
if echo "$ROOT_RESPONSE" | jq -e 'has("message")' > /dev/null; then
    echo "✅ API 루트 응답 성공"
else
    echo "[ERROR] API 루트 응답 오류: $ROOT_RESPONSE"
    exit 1
fi

echo -e "\n=== 2. 서버 헬스 체크 ==="
HEALTH_RESPONSE=$(curl -s -X GET "$API_URL/health")
# 서버 헬스 체크 응답 구조 변경 대응
if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null; then
    echo "✅ 서버 헬스 체크 성공"
else
    echo "[ERROR] 서버 헬스 체크 실패: $HEALTH_RESPONSE"
    exit 1
fi

echo "=== 3. 세션 생성 ==="
SESSION_ID=$(curl -s -X POST "$API_URL/sessions" -H "Content-Type: application/json" -d '{"name": "테스트 세션"}' | jq .id)
echo "[TEST] Created session: $SESSION_ID"
if [ -z "$SESSION_ID" ] || [ "$SESSION_ID" = "null" ]; then
  echo "[ERROR] 세션 생성 실패"
  exit 1
fi

echo -e "\n=== 4. 전체 세션 목록 조회 ==="
SESSIONS=$(curl -s -X GET "$API_URL/sessions")
if echo "$SESSIONS" | jq -e 'type=="array"' > /dev/null; then
    echo "✅ 세션 목록 조회 성공"
else
    echo "[ERROR] 세션 목록 응답 오류: $SESSIONS"
    exit 1
fi

echo -e "\n=== 5. 단일 세션 조회 ==="
SESSION_RESPONSE=$(curl -s -X GET "$API_URL/sessions/$SESSION_ID")
if echo "$SESSION_RESPONSE" | jq -e ".id == $SESSION_ID" > /dev/null; then
    echo "✅ 단일 세션 조회 성공"
else
    echo "[ERROR] 단일 세션 조회 실패: $SESSION_RESPONSE"
    exit 1
fi

echo -e "\n=== 6. 세션에 메시지 추가 ==="
MESSAGE_RES=$(curl -s -X POST "$API_URL/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"content": "테스트 메시지", "role": "user"}')
echo "[TEST] Message add response: $MESSAGE_RES"
MESSAGE_ID=$(echo $MESSAGE_RES | jq '.message.id')
if [ -z "$MESSAGE_ID" ] || [ "$MESSAGE_ID" = "null" ]; then
  echo "[ERROR] 메시지 추가 실패"
  exit 1
fi

echo -e "\n=== 7. 세션 메시지 조회 ==="
MESSAGES_RESPONSE=$(curl -s -X GET "$API_URL/sessions/$SESSION_ID/messages")
if echo "$MESSAGES_RESPONSE" | jq -e 'type=="array"' > /dev/null; then
    echo "✅ 세션 메시지 조회 성공"
else
    echo "[ERROR] 세션 메시지 조회 실패: $MESSAGES_RESPONSE"
    exit 1
fi

echo -e "\n=== 8. 일반 쿼리 처리 ==="
QUERY_RESPONSE=$(curl -s -X POST "$API_URL/query/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"테스트\", \"session_id\": $SESSION_ID, \"limit\": 5}")
if echo "$QUERY_RESPONSE" | jq -e 'has("messages")' > /dev/null; then
    echo "✅ 일반 쿼리 처리 성공"
else
    echo "[ERROR] 일반 쿼리 처리 실패: $QUERY_RESPONSE"
    exit 1
fi

echo -e "\n=== 9. LLM 응답 기반 대화 ==="
CHAT_RESPONSE=$(curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d "{\"messages\": [{\"role\": \"user\", \"content\": \"테스트 메시지\"}]}")
if echo "$CHAT_RESPONSE" | jq -e 'has("response")' > /dev/null; then
    echo "✅ LLM 응답 기반 대화 성공"
else
    echo "[ERROR] LLM 응답 기반 대화 실패: $CHAT_RESPONSE"
    exit 1
fi

echo -e "\n=== 10. 단일 메시지 기반 대화 ==="
SINGLE_CHAT_RESPONSE=$(curl -s -X POST "$API_URL/chat/message" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"테스트 메시지\"}")
if echo "$SINGLE_CHAT_RESPONSE" | jq -e 'has("message")' > /dev/null; then
    echo "✅ 단일 메시지 기반 대화 성공"
else
    echo "[ERROR] 단일 메시지 기반 대화 실패: $SINGLE_CHAT_RESPONSE"
    exit 1
fi

echo -e "\n=== 11. 의미 기반 검색 ==="
SEARCH_RES=$(curl -s -X POST "$API_URL/query/semantic_search" -H "Content-Type: application/json" -d "{\"query\": \"테스트\", \"session_id\": $SESSION_ID, \"limit\": 5}")
echo "[TEST] Semantic search response: $SEARCH_RES"
SEARCH_COUNT=$(echo $SEARCH_RES | jq '.results | length')
if [ "$SEARCH_COUNT" -eq 0 ]; then
  echo "[ERROR] 의미 기반 검색 실패"
  exit 1
fi

echo -e "\n=== 12. 세션 정보 업데이트 ==="
UPDATE_SESSION_RESPONSE=$(curl -s -X PUT "$API_URL/sessions/$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"name": "업데이트된 테스트 세션"}')
if echo "$UPDATE_SESSION_RESPONSE" | jq -e ".name == \"업데이트된 테스트 세션\"" > /dev/null; then
    echo "✅ 세션 정보 업데이트 성공"
else
    echo "[ERROR] 세션 정보 업데이트 실패: $UPDATE_SESSION_RESPONSE"
    exit 1
fi

echo -e "\n=== 13. 메시지 업데이트 ==="
UPDATE_MESSAGE_RESPONSE=$(curl -s -X PUT "$API_URL/sessions/$SESSION_ID/messages/$MESSAGE_ID" \
  -H "Content-Type: application/json" \
  -d '{"content": "업데이트된 메시지입니다!", "role": "user"}')
if echo "$UPDATE_MESSAGE_RESPONSE" | jq -e ".content == \"업데이트된 메시지입니다!\"" > /dev/null; then
    echo "✅ 메시지 업데이트 성공"
else
    echo "[ERROR] 메시지 업데이트 실패: $UPDATE_MESSAGE_RESPONSE"
    exit 1
fi

echo -e "\n=== 14. 메시지 삭제 ==="
DELETE_MESSAGE_RESPONSE=$(curl -s -X DELETE "$API_URL/sessions/$SESSION_ID/messages/$MESSAGE_ID")
if [ $? -eq 0 ]; then
    echo "✅ 메시지 삭제 성공"
else
    echo "[ERROR] 메시지 삭제 실패"
    exit 1
fi

echo -e "\n=== 15. 세션 삭제 ==="
DELETE_SESSION_RESPONSE=$(curl -s -X DELETE "$API_URL/sessions/$SESSION_ID")
if [ $? -eq 0 ]; then
    echo "✅ 세션 삭제 성공"
else
    echo "[ERROR] 세션 삭제 실패"
    exit 1
fi

# OpenAPI Spec 정리
rm -f "$API_DOCS_DIR/openapi.json"

echo "[SUCCESS] 모든 API 테스트가 정상적으로 완료되었습니다." 