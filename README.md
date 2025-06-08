# EchoPrompt

A FastAPI-based application for managing chat sessions with semantic search capabilities.

## Features

- Session management (create, read)
- Message management within sessions
- Semantic search using Qdrant vector database
- OpenAI embeddings integration

## Prerequisites

- Python 3.10+
- Qdrant server (local or cloud)
- OpenAI API key

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/echoprompt.git
cd echoprompt
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
cp .env.example .env
```

5. Update the `.env` file with your configuration:
```
DATABASE_URL=sqlite:///./echoprompt.db
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=your_api_key_here
```

6. Start Qdrant server (required for vector search):
```bash
# Using Docker
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Or using Homebrew (macOS)
brew install qdrant
qdrant
```

---

## ✅ Codex의 주요 역할
- FastAPI 엔드포인트 문서화 (`summary`, `description`, `tags`, `response_model` 명시)
- Pydantic 모델에 필드 설명 추가
- Swagger (`/docs`) 자동화 문서 확인 (구조만)
- OpenAPI 스펙 정합성 확보 (요청/응답 모델 구성)

## 🚫 Codex가 할 필요 없는 작업 (참고만)
- `test_api.sh` 스크립트 **작성/수정**은 가능하지만, **직접 실행은 불필요**
- Qdrant 서버 구동 (Docker 실행)은 필요 없음
- 로컬 DB 초기화, 마이그레이션 수행 필요 없음
- 테스트 자동화 파이프라인 실행 필요 없음

> **테스트 및 서버 운영 환경은 로컬에서 별도로 관리됩니다.**

---

## How to Run (실행 방법)

### 1. FastAPI 서버 실행 (venv 환경에서)
```bash
bash run_app.sh
```
- Qdrant 서버 상태 확인
- venv 활성화
- DB 초기화
- 서버 실행

### 2. API 테스트 (서버가 실행 중일 때)
```bash
bash test_api.sh
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```
- 세션 생성, 메시지 추가, 메시지 조회, 의미 기반 검색을 curl로 테스트합니다.
- 필요에 따라 test_api.sh의 세션 id 값을 수정하세요.

### 3. 단계별 명령어

#### (1) Qdrant 서버 실행
```bash
# Docker 사용
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# 또는 Homebrew 사용 (macOS)
brew install qdrant
qdrant
```

#### (2) venv 환경 활성화
```bash
source venv/bin/activate
```

#### (3) DB 초기화
```bash
python -c "from app.database import create_db_and_tables; create_db_and_tables()"
```

#### (4) FastAPI 서버 실행
```bash
uvicorn app.main:app --reload
```

#### (5) API 테스트
```bash
bash test_api.sh
```

## API Endpoints

### Sessions
- `POST /sessions/` - Create a new session
- `GET /sessions/{session_id}` - Get session details
- `PUT /sessions/{session_id}` - Update session information
- `DELETE /sessions/{session_id}` - Delete a session and related data
- `POST /sessions/{session_id}/messages/` - Add a message to a session
- `GET /sessions/{session_id}/messages/` - Get all messages in a session
- `PUT /sessions/{session_id}/messages/{message_id}` - Update a message
- `DELETE /sessions/{session_id}/messages/{message_id}` - Delete a message

### Query
- `POST /query/semantic_search` - Search messages semantically within a session

## Development

- Code formatting: Black
- Type hints: Python 3.10+
- Database: SQLite with SQLModel ORM
- Vector DB: Qdrant
- API: FastAPI

## License

MIT

# 🧠 echoprompt - 1단계 MVP 준비 사항

---

## ✅ 1단계 목표
> **Git 연동 없이**  
> **긴 대화 프롬프트를 토큰 최적화(RAG+MCP)로 지원하는 시스템 구축**

---

# 🧩 준비해야 할 것 (단계별 정리)

## 1. 프로젝트 세팅
- [ ] 리포지토리 초기화 (`echoprompt`)
- [ ] 기본 디렉토리 구조 설정 (frontend, backend, db, docs)
- [ ] 기술 스택 확정
  - LLM API: OpenAI GPT-4o
  - 벡터DB: Qdrant
  - Backend: FastAPI
  - Frontend: React + TailwindCSS
  - DB: SQLite
- [ ] `.gitignore`, `README.md` 작성

---

## 2. 백엔드 (FastAPI)
- [ ] 세션 생성/조회/저장 API
- [ ] 벡터 임베딩 저장/검색 API
- [ ] LLM 요청 API (최적화된 프롬프트 구성 후 전송)
- [ ] API 문서화 (Swagger/OpenAPI)

---

## 3. 벡터DB (Qdrant)
- [ ] Qdrant 설치 (로컬 or 클라우드)
- [ ] 세션 데이터 임베딩 → Qdrant에 저장
- [ ] 쿼리 → 임베딩 검색 → Top-k 결과 반환

---

## 4. 프론트엔드 (React)
- [ ] 프롬프트 입력창 UI
- [ ] 대화 히스토리 패널
- [ ] 대화 응답 표시 영역
- [ ] 세션 관리 UI (세션 선택/불러오기)

---

## 5. RAG Layer (검색 기반 최적화)
- [ ] 쿼리 기반 과거 대화 검색
- [ ] Top-k 검색 결과 요약 (Summarization)
- [ ] 최적화된 컨텍스트 → LLM 프롬프트 구성

---

## 6. 로컬 프리프로세싱 (선택적)
- [ ] 키워드 추출, 요약 기능 로컬 지원
- [ ] (옵션) LLaMA 3 8B or Mistral 7B 기반 요약

---

## 7. 테스트 및 검증
- [ ] 긴 대화 시나리오 작성
- [ ] 응답 속도/비용 모니터링
- [ ] 토큰 절감 효과 측정

---

## 8. 초기 배포
- [ ] 로컬 테스트 배포 (Docker Compose?)
- [ ] (옵션) 간단한 클라우드 데모 배포 (Vercel/Render)

---

# ✅ 요약
| 항목                  | 설명 |
|:-----------------------|:----|
| 1단계 목표              | 긴 대화 + 토큰 최적화 프롬프트 |
| 개발 스택               | OpenAI GPT-4o + Qdrant + FastAPI + React |
| 핵심 기능               | 대화 세션 관리, 벡터 검색, 최적화 프롬프트 |
| 최종 결과물             | 사용자 프롬프트 → 긴 맥락 대화 가능 |

---

# 🚀 한 줄 요약
> **echoprompt 1단계: 긴 대화 토큰 최적화 RAG+MCP 시스템 구축.**

