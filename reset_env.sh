#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 기존 환경 변수 제거
echo "Resetting environment variables..."
unset VITE_API_HOST
unset VITE_API_PORT
unset VITE_FRONTEND_HOST
unset VITE_FRONTEND_PORT
unset QDRANT_HOST
unset QDRANT_PORT
unset OPENAI_API_KEY
unset OPENAI_ORGANIZATION_ID
unset OPENAI_CHAT_MODEL
unset OPENAI_EMBEDDING_MODEL
unset DATABASE_HOST
unset DATABASE_PORT
unset DATABASE_NAME

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

# URL 환경 변수 생성
echo "Generating URL environment variables..."

# API URL
if [ -n "$VITE_API_PORT" ]; then
    export VITE_API_URL="http://${VITE_API_HOST}:${VITE_API_PORT}"
else
    export VITE_API_URL="http://${VITE_API_HOST}"
fi

# Frontend URL
if [ -n "$VITE_FRONTEND_PORT" ]; then
    export VITE_FRONTEND_URL="http://${VITE_FRONTEND_HOST}:${VITE_FRONTEND_PORT}"
else
    export VITE_FRONTEND_URL="http://${VITE_FRONTEND_HOST}"
fi

# Qdrant URL
if [ -n "$QDRANT_PORT" ]; then
    export QDRANT_URL="http://${QDRANT_HOST}:${QDRANT_PORT}"
else
    export QDRANT_URL="http://${QDRANT_HOST}"
fi

# Database URL
if [[ "$DATABASE_HOST" == sqlite:///* ]]; then
    export DATABASE_URL="$DATABASE_HOST"
else
    if [ -n "$DATABASE_PORT" ]; then
        export DATABASE_URL="postgresql://${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}"
    else
        export DATABASE_URL="postgresql://${DATABASE_HOST}/${DATABASE_NAME}"
    fi
fi

# 현재 환경 변수 값 출력
echo -e "\nCurrent environment variables:"
echo -e "${GREEN}VITE_API_URL: ${VITE_API_URL}${NC}"
echo -e "${GREEN}VITE_FRONTEND_URL: ${VITE_FRONTEND_URL}${NC}"
echo -e "${GREEN}QDRANT_URL: ${QDRANT_URL}${NC}"
echo -e "${GREEN}DATABASE_URL: ${DATABASE_URL}${NC}"

echo -e "\n${GREEN}Environment variables have been reset successfully!${NC}" 