#!/bin/bash

# 서버 상태 확인 함수
check_server() {
    local max_attempts=3
    local attempt=1
    local wait_time=2

    echo "서버 상태 확인 중..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://127.0.0.1:8000/docs" > /dev/null; then
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
if curl -s -f "http://127.0.0.1:8000/docs" > /dev/null; then
    echo "✅ Swagger UI 접근 성공"
else
    echo "❌ Swagger UI 접근 실패"
    exit 1
fi

echo -e "\n2. OpenAPI Spec 다운로드"
if curl -s -f -o openapi.json "http://127.0.0.1:8000/openapi.json"; then
    echo "✅ OpenAPI Spec 다운로드 성공"
    # OpenAPI Spec에서 엔드포인트 목록 추출
    echo -e "\n3. API 엔드포인트 목록:"
    grep -o '"path":"[^"]*"' openapi.json | sed 's/"path":"//g' | sed 's/"//g'
else
    echo "❌ OpenAPI Spec 다운로드 실패"
    exit 1
fi

echo "=== 1. 세션 생성 ==="
SESSION_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/sessions/" \
  -H "Content-Type: application/json" \
  -d '{"name": "테스트 세션"}')
echo "응답: $SESSION_RESPONSE"

# 세션 ID 추출
SESSION_ID=$(echo $SESSION_RESPONSE | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
if [ -z "$SESSION_ID" ]; then
    echo "세션 생성 실패"
    exit 1
fi
echo "생성된 세션 ID: $SESSION_ID"

echo -e "\n=== 2. 세션에 메시지 추가 ==="
MESSAGE_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/sessions/$SESSION_ID/messages/" \
  -H "Content-Type: application/json" \
  -d '{"content": "안녕하세요!", "role": "user"}')
echo "응답: $MESSAGE_RESPONSE"

# 메시지 ID 추출
MESSAGE_ID=$(echo $MESSAGE_RESPONSE | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
if [ -z "$MESSAGE_ID" ]; then
    echo "메시지 추가 실패"
    exit 1
fi
echo "생성된 메시지 ID: $MESSAGE_ID"

echo -e "\n=== 3. 세션 메시지 조회 ==="
MESSAGES_RESPONSE=$(curl -s -X GET "http://127.0.0.1:8000/sessions/$SESSION_ID/messages/")
echo "응답: $MESSAGES_RESPONSE"

echo -e "\n=== 4. 의미 기반 검색 ==="
SEARCH_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/query/semantic_search" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"안녕?\", \"session_id\": $SESSION_ID, \"limit\": 3}")
echo "응답: $SEARCH_RESPONSE"

echo -e "\n=== 5. 세션 정보 업데이트 ==="
UPDATE_SESSION_RESPONSE=$(curl -s -X PUT "http://127.0.0.1:8000/sessions/$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"name": "업데이트된 테스트 세션"}')
echo "응답: $UPDATE_SESSION_RESPONSE"

echo -e "\n=== 6. 메시지 업데이트 ==="
UPDATE_MESSAGE_RESPONSE=$(curl -s -X PUT "http://127.0.0.1:8000/sessions/$SESSION_ID/messages/$MESSAGE_ID" \
  -H "Content-Type: application/json" \
  -d '{"content": "업데이트된 메시지입니다!", "role": "user"}')
echo "응답: $UPDATE_MESSAGE_RESPONSE"

echo -e "\n=== 7. 메시지 삭제 ==="
DELETE_MESSAGE_RESPONSE=$(curl -s -X DELETE "http://127.0.0.1:8000/sessions/$SESSION_ID/messages/$MESSAGE_ID")
echo "응답 상태 코드: $?"

echo -e "\n=== 8. 세션 삭제 ==="
DELETE_SESSION_RESPONSE=$(curl -s -X DELETE "http://127.0.0.1:8000/sessions/$SESSION_ID")
echo "응답 상태 코드: $?"

# OpenAPI Spec 정리
rm -f openapi.json 