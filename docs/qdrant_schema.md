
# 📌 GitHub Issues for Multi-Agent Project Contribution (Cursor, Codex, Jules)

---

## 🧩 Issue 1: [Cursor] 기존 FastAPI 백엔드에 새로운 Qdrant 스키마 통합

**🎯 목표**  
기존 `query_router.py` 및 `qdrant_client.py` 코드에 새로운 `VectorPayload` 구조를 반영하고, 불필요한 필드를 제거하며 전체 삽입/검색 흐름을 업데이트합니다.

**✅ 작업 항목**
- [ ] `routers/query_router.py`에서 `payload` 구성 필드를 `VectorPayload`에 맞게 수정
- [ ] `qdrant_client.py` 내 insert/search 관련 함수 리팩토링
- [ ] `summary`, `token_count`, `memory_type` 필드 반영
- [ ] 환경 변수로부터 `embedding_model` 가져오는 로직 추가
- [ ] 전체 삽입 → 검색 → 응답 흐름 테스트

**📎 참고**
- 스키마 정의 문서: `docs/qdrant_schema.md`
- 기존 삽입 함수: `qdrant_client.py`

---

## ⚙️ Issue 2: [Codex] 벡터 저장용 스키마 및 삽입/검색/요약 함수 생성

**🎯 목표**  
Qdrant에 벡터를 저장하고 검색하는 데 필요한 Pydantic 모델 및 함수들을 새로 생성합니다.

**✅ 작업 항목**
- [ ] `models/vector_payload.py` 생성 및 `VectorPayload` 클래스 정의
- [ ] `utils/token_utils.py`에 `count_tokens(text)` 함수 구현 (tiktoken 기반)
- [ ] `qdrant_client.py`에 `insert_vector()`, `search_vectors()` 함수 새로 작성
- [ ] 간단한 FastAPI 라우터 예제 작성 (선택)

**📎 참고 예시**
```python
class VectorPayload(BaseModel):
    user_id: str
    session_id: int
    message_id: int
    ...
```

---

## 🧠 Issue 3: [Jules] 스키마 구조 및 검색 흐름 문서화

**🎯 목표**  
전체 시스템의 검색 흐름 및 벡터 스키마 구조를 명확하게 문서화합니다.

**✅ 작업 항목**
- [ ] `docs/qdrant_schema.md` 작성 (필드별 설명 포함)
- [ ] `docs/search_flow.md` 작성 (short_term → long_term → summary 흐름)
- [ ] README에 "Qdrant 기반 의미 검색 구조" 섹션 추가
- [ ] 테스트 시나리오 명세 (`docs/use_cases.md`)

**📎 예시 흐름**
```text
[ 사용자 질의 입력 ]
      ↓
[ 1차 검색: short_term ]
      ↓
[ 2차 검색: summary ]
      ↓
[ 컨텍스트 구성 → LLM 호출 ]
```

---

각 이슈는 레포지토리에 직접 등록하거나, GitHub CLI / REST API로 자동 등록 가능합니다.
