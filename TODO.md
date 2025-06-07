# TODO: API 엔드포인트 구현 목록

## 1. 의미 기반 검색 API
- [ ] `/query/semantic_search` 엔드포인트 구현
  - 입력: 검색 쿼리 문자열
  - 기능: 
    - 쿼리 텍스트의 임베딩 생성
    - Qdrant를 사용한 벡터 검색
    - 유사도 기반 메시지 검색
  - 출력: 검색된 메시지 목록 (유사도 점수 포함)

## 2. 세션 관리 API 개선
- [ ] 세션 삭제 기능
  - [ ] `/sessions/{session_id}` DELETE 엔드포인트
  - [ ] 관련 메시지 및 임베딩 데이터 정리

- [ ] 세션 수정 기능
  - [ ] `/sessions/{session_id}` PUT 엔드포인트
  - [ ] 세션 이름 등 정보 수정

## 3. 메시지 관리 API 개선
- [ ] 메시지 삭제 기능
  - [ ] `/sessions/{session_id}/messages/{message_id}` DELETE 엔드포인트
  - [ ] Qdrant에서 관련 임베딩 데이터 정리

- [ ] 메시지 수정 기능
  - [ ] `/sessions/{session_id}/messages/{message_id}` PUT 엔드포인트
  - [ ] 메시지 내용 수정 시 임베딩 재생성

## 4. 에러 처리 개선
- [ ] 상세한 에러 메시지 구현
- [ ] 적절한 HTTP 상태 코드 사용
- [ ] 입력값 유효성 검사 강화

## 5. API 문서화
- [ ] Swagger/OpenAPI 문서 자동 생성
- [ ] API 사용 예제 추가
- [ ] 각 엔드포인트의 요청/응답 스키마 상세화 