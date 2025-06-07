# Troubleshooting Log (2024-06-07)

## 문제 요약
- 세션/메시지 관련 API 호출 시 Internal Server Error 발생
- 서버 로그에서 다음과 같은 AttributeError가 반복적으로 발생함:
  - `'SessionModel' object has no attribute 'query'`
- FastAPI의 의존성 주입이 꼬여서 db에 Session이 아닌 SessionModel 인스턴스가 주입되고 있음

## 현재까지의 시도
- 엔드포인트 함수의 이름을 모두 변경하여 get_session 등과의 충돌 방지
- db: Session = Depends(get_session) 파라미터를 항상 첫 번째로 배치
- 여전히 동일한 에러 발생

## 원인 추정
- APIRouter의 prefix가 `/sessions`인데, 각 엔드포인트 경로도 `/sessions/...`로 시작하고 있음
- 이로 인해 FastAPI가 라우팅/DI를 잘못 매칭할 수 있음

## 해결 방안(예정)
- 라우터의 prefix는 `/sessions`로 두고, 엔드포인트 경로에서는 `/sessions`를 제거
  - 예: `@router.post("/")`, `@router.get("/{session_id}")` 등
- 수정 후 서버 재시작 및 테스트 예정 