#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# 서버 상태 확인 함수
check_server() {
    local url=$1
    local max_attempts=3
    local attempt=1
    local wait_time=2

    echo "서버 상태 확인 중..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null; then
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