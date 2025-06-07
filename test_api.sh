#!/bin/bash

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

echo -e "\n=== 3. 세션 메시지 조회 ==="
MESSAGES_RESPONSE=$(curl -s -X GET "http://127.0.0.1:8000/sessions/$SESSION_ID/messages/")
echo "응답: $MESSAGES_RESPONSE"

echo -e "\n=== 4. 의미 기반 검색 ==="
SEARCH_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/query/semantic_search" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"안녕?\", \"session_id\": $SESSION_ID, \"top_k\": 3}")
echo "응답: $SEARCH_RESPONSE" 