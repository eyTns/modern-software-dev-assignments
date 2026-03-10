# Week 3 — DJMAX Respect V MCP Server

[V-Archive](https://v-archive.net) API를 감싸는 MCP(Model Context Protocol) 서버입니다.
Claude Desktop, Cursor 등 MCP 호환 클라이언트에서 DJMAX Respect V 유저 기록을 자연어로 조회할 수 있습니다.

## Prerequisites

- Python 3.10 이상
- 루트 프로젝트의 가상 환경(`.venv`)에 `mcp[cli]`, `httpx` 설치

## 환경 설정 및 실행

```bash
# 프로젝트 루트에서
cd modern-software-dev-assignments
& .venv/Scripts/Activate.ps1
uv pip install "mcp[cli]" httpx

# 서버 실행 (STDIO 모드)
python week3/server/main.py
```

## Claude Desktop 설정

`claude_desktop_config.json`에 아래 내용을 추가합니다.

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "varchive": {
      "command": "C:\\YOUR\\PROJECT\\PATH\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\YOUR\\PROJECT\\PATH\\week3\\server\\main.py"
      ]
    }
  }
}
```

## MCP Inspector로 테스트

```bash
# 프로젝트 루트에서 (venv 활성화 상태)
npx @modelcontextprotocol/inspector .venv/Scripts/python.exe week3/server/main.py
```

## Tool 레퍼런스

### `get_user_tier`

V-Archive에 등록된 유저의 버튼별 티어 정보를 조회합니다.

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `nickname` | string | V-Archive 닉네임 |
| `button` | integer | 버튼 모드 (4, 5, 6, 8) |

**예시 입력**

```json
{ "nickname": "eyTns", "button": 6 }
```

**예시 출력**

```
[eyTns] 6B 티어 정보
  현재 티어: Master III (M)
  티어 포인트: 9,749.90
  상위 50곡 합산: 9,568.5486
  다음 티어: Master II (필요 포인트: 50.10)

  상위 곡 (총 50곡 중 상위 5곡):
    1. Ikazuchi [6B SC Lv.14] — 99.96% (rating 196.055)
    2. Hell'o [6B SC Lv.15] — 99.87% (rating 195.283)
    3. Garakuta Doll Play [6B SC Lv.14] — 99.93% (rating 195.114)
    4. LIMBO [6B SC Lv.15] — 99.86% (rating 194.994)
    5. Disappearing Act [6B SC Lv.14] — 99.98% (rating 194.715)
```

**에러 케이스**

- 닉네임이 존재하지 않을 때: `"닉네임 찾을 수 없음"`
- 잘못된 버튼 값: `"잘못된 버튼 값입니다: 7. 4, 5, 6, 8 중 하나를 선택해 주세요."`
- 해당 버튼 티어 데이터 없음: `"해당 버튼의 티어 데이터가 없습니다."`

---

### `get_user_song_record`

특정 곡에 대한 유저의 버튼/난이도별 기록을 조회합니다.

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `nickname` | string | V-Archive 닉네임 |
| `title_num` | integer | 곡 ID (`search_songs`로 확인 가능) |

**예시 입력**

```json
{ "nickname": "eyTns", "title_num": 555 }
```

**예시 출력**

```
[eyTns] Gloxinia
  작곡: Ruxxi, Milkoi
  DLC: V EXTENSION 4

  4B NM Lv.5 — 기록 없음
  4B HD Lv.8 — 기록 없음
  4B MX Lv.11 — 기록 없음
  4B SC Lv.10 — 100.00% | MAX COMBO | rating 178 | DJ Power 77.79
  5B NM Lv.7 — 기록 없음
  5B HD Lv.9 — 기록 없음
  5B MX Lv.12 — 기록 없음
  5B SC Lv.11 — 99.81% | MAX COMBO | rating 176.174 | DJ Power 81.4899
  6B NM Lv.5 — 기록 없음
  6B HD Lv.9 — 기록 없음
  6B MX Lv.11 — 기록 없음
  6B SC Lv.10 — 100.00% | MAX COMBO | rating 178 | DJ Power 77.79
  8B NM Lv.5 — 기록 없음
  8B HD Lv.8 — 기록 없음
  8B MX Lv.13 — 기록 없음
  8B SC Lv.10 — 99.95% | MAX COMBO | rating 177.943 | DJ Power 77.6604
```

**에러 케이스**

- 닉네임 없음: `"닉네임 찾을 수 없음"`
- 곡 번호 없음: `"title 찾을 수 없음"`

---

### `search_songs`

곡 이름으로 DJMAX Respect V 곡을 검색합니다. 대소문자를 구분하지 않으며 부분 일치로 검색합니다.

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `query` | string | 검색할 곡 이름 (부분 일치) |

**예시 입력**

```json
{ "query": "glory" }
```

**예시 출력**

```
검색 결과: 'glory' (4건)
  [16] glory day — BEXTER / Mycin.T (RESPECT)
  [410] glory day (Mintorment Remix) — Mintorment (PORTABLE 3)
  [411] glory day -JHS Remix- — JHS (PORTABLE 3)
  [594] glory MAX -나의 최대치로 너와 함께할게- — TAK (V EXTENSION 5)
```

> 곡 ID(`[16]`)를 `get_user_song_record`의 `title_num`에 사용할 수 있습니다.

**에러 케이스**

- 검색 결과 없음: `"'xyz'에 해당하는 곡을 찾을 수 없습니다."`

---

### `refresh_songs`

로컬에 캐시된 곡 목록 DB를 강제로 갱신합니다. 파라미터 없이 호출합니다.

**예시 출력**

```
곡 목록을 갱신했습니다. 총 420곡이 저장되었습니다.
```

> 곡 목록은 최초 검색 시 자동으로 다운로드되며, 5일이 경과하면 자동 갱신됩니다.

## 예시 호출 흐름

### 티어 조회

> 사용자: "eyTns의 6버튼 티어 알려줘"

1. LLM이 `get_user_tier(nickname="eyTns", button=6)` 호출
2. 티어 정보 반환

### 곡 기록 조회 (곡 이름만 알 때)

> 사용자: "eyTns의 글로리데이 기록 알려줘"

1. LLM이 `search_songs(query="glory day")` 호출 → 곡 ID 확인
2. LLM이 `get_user_song_record(nickname="eyTns", title_num=16)` 호출
3. 기록 반환

## 사용 API

- 유저 티어 조회: `GET https://v-archive.net/api/archive/{nickname}/tier/{button}`
- 유저 곡별 기록 조회: `GET https://v-archive.net/api/archive/{nickname}/title/{titleNum}`
- 곡 목록 DB: `https://v-archive.net/db/songs.json`

API 문서: [v-archive.net/info/api](https://v-archive.net/info/api)
