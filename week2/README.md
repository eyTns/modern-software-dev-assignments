# Action Item Extractor

회의록이나 메모를 입력하면 실행 가능한 할 일(action item)을 자동으로 추출해주는 웹 애플리케이션입니다. 규칙 기반(heuristic) 추출과 LLM 기반 추출 두 가지 방식을 지원합니다.

## 기술 스택

- **백엔드** — FastAPI, SQLite, Pydantic
- **LLM** — Ollama (로컬 모델 추론)
- **프론트엔드** — 단일 HTML 파일 (vanilla JS)
- **테스트** — pytest

## 프로젝트 구조

```
week2/
├── app/
│   ├── main.py              # FastAPI 앱 진입점, lifespan 이벤트
│   ├── db.py                # SQLite 데이터베이스 레이어
│   ├── schemas.py           # Pydantic 요청/응답 모델
│   ├── routers/
│   │   ├── action_items.py  # 액션 아이템 관련 엔드포인트
│   │   └── notes.py         # 노트 관련 엔드포인트
│   └── services/
│       └── extract.py       # 추출 로직 (heuristic + LLM)
├── frontend/
│   └── index.html           # 웹 프론트엔드
├── tests/
│   └── test_extract.py      # 추출 함수 테스트
└── data/
    └── app.db               # SQLite DB 파일 (자동 생성)
```

## 설치 및 실행

### 사전 요구사항

- Python 3.10 이상
- Ollama (LLM 추출 기능 사용 시)

### 환경 설정

```bash
# 의존성 설치
poetry install

# Ollama 모델 다운로드 (LLM 추출에 필요)
ollama pull llama3.1:8b
```

### 서버 실행

```bash
poetry run uvicorn week2.app.main:app --reload
```

브라우저에서 http://127.0.0.1:8000/ 으로 접속합니다.

## API 엔드포인트

### 노트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/notes` | 새 노트 생성 |
| `GET` | `/notes` | 전체 노트 목록 조회 |
| `GET` | `/notes/{note_id}` | 특정 노트 조회 |

**POST /notes** 요청 예시
```json
{ "content": "회의 내용..." }
```

### 액션 아이템

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/action-items/extract` | 규칙 기반 추출 |
| `POST` | `/action-items/extract-llm` | LLM 기반 추출 |
| `GET` | `/action-items` | 전체 액션 아이템 조회 (note_id 필터 가능) |
| `POST` | `/action-items/{id}/done` | 완료 상태 토글 |

**POST /action-items/extract** 요청 예시
```json
{ "text": "- [ ] DB 설정\n- API 구현\ntodo: 테스트 작성", "save_note": true }
```

**POST /action-items/{id}/done** 요청 예시
```json
{ "done": true }
```

### 추출 방식 비교

- **규칙 기반** (`/extract`) — 불릿, 체크박스, 키워드 접두사(`todo:`, `action:`, `next:`), 명령형 문장을 패턴 매칭으로 추출합니다. 외부 의존성 없이 동작합니다.
- **LLM 기반** (`/extract-llm`) — Ollama를 통해 로컬 LLM에 텍스트를 전달하고, JSON 형식으로 액션 아이템을 받아옵니다. 기본 모델은 `llama3.1:8b`입니다.

## 테스트 실행

```bash
poetry run pytest week2/tests/ -v
```

LLM 테스트는 Ollama에 해당 모델이 설치되어 있어야 실행됩니다. 모델이 없으면 자동으로 건너뜁니다.
