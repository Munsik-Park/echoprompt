
# Frontend Playwright 테스트 문제점

## 1. 하이라이트 애니메이션 관련 문제
- 하이라이트 애니메이션이 비동기적으로 표시되도록 구현되어 있으나, 실제 동영상에서는 보이지 않는 문제 발생
- 테스트는 하이라이트를 체크하고 있으나, 실제 UI에서는 하이라이트가 제대로 표시되지 않음
- LLM 응답이 먼저 보이고 하이라이트가 늦게 나와서 테스트가 실패하는 경우 발생

## 2. 타이밍 이슈
- 하드코딩된 대기 시간(30초)이 실제 환경에서는 부적절할 수 있음
- UI 상태 업데이트와 테스트 검증 사이의 타이밍 불일치
- 비동기 작업(API 호출, 상태 업데이트)의 완료를 제대로 기다리지 못하는 경우 발생

## 3. 테스트 안정성 문제
- 테스트 실행 시 환경 변수 설정이 일관되지 않음
- 프론트엔드 서버 시작과 테스트 실행 사이의 타이밍 이슈
- 세션 정리 후에도 일부 세션이 남아있는 경우 발생

## 4. 테스트 구조적 문제
- 테스트 케이스 간의 의존성으로 인한 불안정성
- 하드코딩된 선택자와 데이터 테스트 ID의 불일치
- 에러 발생 시 디버깅이 어려운 구조

## 5. 환경 설정 문제
- 환경 변수(VITE_API_URL, VITE_FRONTEND_URL)가 제대로 설정되지 않는 경우 발생
- 프론트엔드 서버 시작 시 환경 변수 로드 실패
- 테스트 실행 환경과 개발 환경의 설정 불일치

## 6. 세션 관리 문제
- 테스트 전 세션 정리가 완전히 이루어지지 않는 경우
- 세션 삭제 후 UI 업데이트가 즉시 반영되지 않는 문제
- 세션 카운트 검증이 실제 상태와 불일치하는 경우

## 7. UI 상태 검증 문제
- 메시지 렌더링 순서와 테스트 검증 순서의 불일치
- 로딩 스피너 상태 변경 감지 실패
- 채팅 윈도우 렌더링 타이밍 문제

## 8. 테스트 실행 환경 문제
- 셸 변경으로 인한 환경 변수 유실
- 백그라운드 프로세스 관리 문제
- 테스트 실행 중 서버 상태 불안정

## 해결 방향
1. 테스트 안정성 개선
   - 동적 대기 시간 설정
   - 상태 기반 검증 로직 구현
   - 재시도 메커니즘 도입

2. 환경 설정 강화
   - 환경 변수 검증 로직 추가
   - 테스트 실행 전 환경 체크
   - 서버 상태 확인 메커니즘 개선

3. 테스트 구조 개선
   - 테스트 케이스 독립성 확보
   - 선택자 관리 체계화
   - 에러 로깅 강화

4. UI 상태 관리 개선
   - 상태 변경 이벤트 기반 검증
   - 비동기 작업 완료 확인 메커니즘
   - UI 업데이트 타이밍 조정

