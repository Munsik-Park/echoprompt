
# 🧠 작업 세션 관리 플로우 (이슈 기반 RAG 시스템)

## ✅ 너가 원하는 완성된 그림
1. 문제 해결되면
   - 세션(이슈)은 날려버리는 게 아니라 **스토리지에 저장**.
2. 필요하면
   - **검색**해서 과거 이슈/코드/해결 흐름을 다시 꺼내오기.
3. 단순 저장이 아니라
   - **RAG**(Retrieval-Augmented Generation) 방식으로, 과거 이슈를 GPT가 참조할 수 있게.
4. 즉:
   - (a) 큰 코딩 흐름은 세션으로 남긴다.
   - (b) 문제 해결된 이슈는 스토리지에 저장.
   - (c) 필요할 때 빠르게 검색 + 로딩해서 이어서 작업.

## ✅ RAG + 세션 스위치

### 📚 RAG (Retrieval-Augmented Generation)
- LLM이 검색 기반 지식을 참조해서 답변하게 한다.

### 📚 세션 스위치
- 현재 작업 중 이슈 세션을 교체하거나,
- 과거 세션 검색 → 이어받기.

## ✅ 최종 시스템 플로우
```mermaid
flowchart TD
  UserInput([User 작업 시작])
  CreateSession[새로운 이슈 세션 생성]
  Work[작업 + 디버깅 진행]
  IssueResolved[문제 해결]
  StoreToDB[세션 저장 (스토리지)]
  SearchPast[과거 세션 검색]
  LoadSession[선택한 세션 로드]
  ContinueWork[계속 작업]

  UserInput --> CreateSession --> Work
  Work --> IssueResolved --> StoreToDB
  SearchPast --> LoadSession --> ContinueWork
```

## ✅ 스토리지 + 검색 구조

| 기술 스택                  | 역할                                                |
|:----------------------------|:--------------------------------------------------|
| **벡터 DB (Qdrant, Chroma)** | 과거 이슈를 벡터화해서 저장 + 빠른 검색            |
| **로컬 Markdown 저장**      | 코드, 요약문, 해결책을 파일로 저장 (백업/버전 관리) |
| **검색 인덱스**              | 제목, 키워드로 빠른 검색 (Whoosh, Elastic 등)       |
| **RAG 구성**                 | 검색한 결과를 LLM에게 컨텍스트로 주입               |

## ✅ 저장 포맷 예시 (Markdown or JSON)
\`\`\`markdown
# 이슈: 로그인 API 에러 500
- 발생 일시: 2025-06-06
- 원인: DB 연결 실패
- 해결방법:
  1. DB Connection Pool 수정
  2. 에러 핸들링 개선
- 관련 코드 스냅샷:
\`\`\`python
def connect_db():
    try:
        conn = create_connection()
    except Exception as e:
        logger.error(f"Connection error: {e}")
\`\`\`
- 태그: [API], [DB], [500 Error]
\`\`\`

## ✅ 요약
**"문제가 해결되면 세션은 스토리지에 저장하고, 나중에 검색+참조해서 큰 작업 흐름을 이어간다."**
