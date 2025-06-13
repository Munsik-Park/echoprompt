# ⚙️ Jules 작업 지시서

## 역할: 백엔드 FastAPI 기능 구현 및 Qdrant 연동

### ✅ 주요 작업 항목
1. `/sessions/{session_id}/tree` API 구현 (document_id 기반 트리 구성)
2. `/collections`, `/collections/{name}/users`, `/users/{id}/sessions` API 추가
3. Qdrant `payload` 필드로 user_id, session_id 필터 처리
4. Multi-Stage RAG 검색 (short_term → summary → long_term)
5. GPT 응답에 `retrieved_chunks` 필드 포함

### 🗂️ 데이터 구조 참고
- 메시지 트리: document_id + created_at 기반 정렬
- user_id는 의미 없는 숫자이므로 매핑 또는 alias 고려
