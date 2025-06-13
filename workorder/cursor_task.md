# 🖥️ Cursor 작업 지시서

## 역할: React 프론트엔드 UI 및 통합 테스트 담당

### ✅ 주요 작업 항목
1. **CollectionSelector 컴포넌트 구현**
2. **UserSelector 컴포넌트 개선**
3. **SessionList 동적 로딩 구현**
4. **ChatTree 컴포넌트 도입**
5. **SemanticSearch UI 확장**
6. **ContextDisplay 컴포넌트 구현**
7. **전체 흐름 통합 테스트 (Jest, Playwright, Cypress)**

### 🧭 UI 초기 동작 흐름
- 로컬 저장소에 user_id 확인 → 없으면 UUID 생성
- 콜렉션 → 사용자 → 세션 선택 → 메시지 트리 로딩 → 메시지 입력 및 전송 가능
- 상태별 안내 메시지와 컴포넌트 비활성화 상태 필요
