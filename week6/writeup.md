# Week 6 Write-up
Tip: To preview this markdown file
- On Mac, press `Command (⌘) + Shift + V`
- On Windows/Linux, press `Ctrl + Shift + V`

## Instructions

Fill out all of the `TODO`s in this file.

## Submission Details

Name: violet \
SUNet ID: **TODO** \
Citations: **TODO**

This assignment took me about **TODO** hours to do. 


## Brief findings overview 
> TODO

## Fix #1
a. File and line(s)

- `week6/backend/app/routers/notes.py:71`
- `week6/backend/app/routers/notes.py:72`
- `week6/backend/app/routers/notes.py:80`
- `week6/backend/app/routers/notes.py:33`
- `week6/backend/app/routers/action_items.py:33`

b. Rule/category Semgrep flagged

- SAST / SQL Injection (`python.sqlalchemy.security.sqlalchemy-execute-raw-query`)
- SAST / SQL Injection with SQLAlchemy (Pro rule, Critical)
- SAST / `avoid-sqlalchemy-text` (Medium) — `sqlalchemy.text()`에 사용자 입력이 도달할 수 있다는 규칙으로, 71번 줄에서 탐지되었습니다
- 동일 함수 내에서 f-string SQL 조립(72번 줄)과 `db.execute()` 호출(80번 줄)이 각각 탐지되었습니다.
- `notes.py:33`, `action_items.py:33`도 SQL Injection으로 탐지되었으나, ORM `select()` 문을 사용하고 있어 파라미터화가 자동 적용되므로 **false positive로 판단**하여 Ignored 처리했습니다.

c. Brief risk description

`unsafe_search` 엔드포인트가 사용자 입력(`q`)을 f-string으로 SQL 쿼리에 직접 삽입하고 있어, 공격자가 `' OR 1=1 --` 같은 입력으로 전체 데이터를 탈취하거나, UNION 공격으로 DB 스키마를 유출하거나, 데이터를 삭제할 수 있습니다.

d. Your change (short code diff or explanation, AI coding tool usage)

`/unsafe-search` 엔드포인트 전체를 삭제했습니다. (Claude Code 사용). 프론트엔드(`app.js`)와 테스트 코드 어디에서도 이 엔드포인트를 호출하지 않아 삭제해도 기능에 영향이 없습니다. 이미 `list_notes`의 `q` 파라미터가 ORM `.contains()`를 사용해 동일한 검색 기능을 안전하게 제공하고 있으므로, 파라미터 바인딩으로 수정하는 대신 중복 엔드포인트를 제거하는 것이 근본적 해결입니다.

e. Why this mitigates the issue

취약한 코드 자체가 제거되어 SQL Injection 공격 경로가 사라졌습니다. 검색 기능은 ORM 기반의 `list_notes`가 대체하며, SQLAlchemy ORM은 내부적으로 파라미터화된 쿼리를 생성하여 사용자 입력이 SQL 구문으로 해석되지 않습니다.

## Fix #2
a. File and line(s)

- `week6/backend/app/routers/notes.py:104`
- `week6/backend/app/routers/notes.py:112`

b. Rule/category Semgrep flagged

- SAST / Code Injection with FastAPI (Pro rule, Critical) — `eval()`로 사용자 입력을 실행하여 임의 코드 실행이 가능합니다
- SAST / `eval-detected` (Low) — 같은 `eval()` 호출에 대한 커뮤니티 규칙입니다
- SAST / OS Command Injection with FastAPI (Pro rule, High) — `subprocess.run(shell=True)`로 사용자 입력을 셸 명령으로 실행하여 시스템 장악이 가능합니다
- SAST / `subprocess-shell-true` (Medium) — 같은 `subprocess.run(shell=True)` 호출에 대한 커뮤니티 규칙입니다

c. Brief risk description

두 엔드포인트 모두 사용자 입력을 그대로 코드/명령으로 실행합니다. `/debug/eval?expr=__import__('os').system('rm -rf /')` 같은 요청으로 서버에서 임의 코드를 실행할 수 있고, `/debug/run?cmd=cat /etc/passwd`로 시스템 명령을 실행할 수 있습니다. 이 두 가지는 입력을 검증하더라도 근본적으로 안전하게 만들 수 없는 유형의 취약점입니다.

d. Your change (short code diff or explanation, AI coding tool usage)

`/debug/eval`, `/debug/run` 엔드포인트를 모두 삭제했습니다 (Claude Code 사용). 프론트엔드와 테스트 코드 어디에서도 호출하지 않아 기능에 영향이 없습니다. `eval()`과 `subprocess.run(shell=True)`은 사용자 입력을 받는 한 어떤 검증으로도 안전하게 만들 수 없으므로, 삭제가 유일한 해결책입니다.

e. Why this mitigates the issue

임의 코드 실행과 OS 명령 주입의 공격 경로가 사라졌습니다. 이 기능들은 디버그 용도이며 프로덕션에 노출되어서는 안 되는 엔드포인트입니다.

## Fix #3
a. File and line(s)

- `week6/requirements.txt:9`

b. Rule/category Semgrep flagged

- SCA / CVE-2023-23934 - Improper Input Validation
- SCA / CVE-2024-34069 - CSRF, EPSS 41.9%로 가장 높은 위험도
- SCA / CVE-2024-49766 - Path Traversal
- SCA / CVE-2025-66221 - Improper Handling of Windows Device Names
- SCA / CVE-2026-21860 - Improper Handling of Windows Device Names
- SCA / CVE-2026-27199 - Improper Handling of Windows Device Names
- 총 6건이 모두 `Werkzeug==0.14.1`에서 탐지되었습니다.

c. Brief risk description

Werkzeug 0.14.1은 2018년 릴리스로, CSRF, Path Traversal, Input Validation 등 다양한 유형의 CVE가 누적되어 있습니다. 이 앱에서 werkzeug를 직접 import하거나 사용하는 코드는 없지만, 취약한 버전이 설치되어 있는 것 자체가 공급망 공격 표면을 넓힙니다. 다른 패키지가 내부적으로 werkzeug에 의존할 수 있고, 설치 시점에서도 위험이 발생할 수 있습니다.

d. Your change (short code diff or explanation, AI coding tool usage)

`requirements.txt`에서 `Werkzeug==0.14.1`을 `Werkzeug==3.1.6`으로 업그레이드했습니다. Claude Code 사용. 코드베이스에서 werkzeug를 직접 사용하는 곳이 없음을 확인했으므로 호환성 문제는 없습니다. 테스트 3건 모두 통과했습니다.

e. Why this mitigates the issue

최신 버전 3.1.6에는 위 6건의 CVE가 모두 패치되어 있습니다. 의존성 업그레이드는 SCA 취약점의 표준적인 해결 방법이며, 사용하지 않는 패키지라면 제거하는 것도 대안이지만, 과제 의도에 맞춰 버전 업그레이드로 처리했습니다.




## 의도적으로 삽입된 취약점 목록 (by Claude Code)

| # | 카테고리 | 위치 | 취약점 |
|---|---------|------|--------|
| 1 | SAST | `notes.py:69-92` | SQL Injection - f-string으로 쿼리 조립 |
| 2 | SAST | `notes.py:102-105` | `eval()` 임의 코드 실행 |
| 3 | SAST | `notes.py:108-113` | `subprocess.run(shell=True)` 명령어 주입 |
| 4 | SAST | `notes.py:116-122` | `urlopen(url)` SSRF |
| 5 | SAST | `notes.py:125-131` | `open(path)` Path Traversal |
| 6 | SAST | `notes.py:95-99` | MD5 해싱 - 약한 암호화 |
| 7 | SAST | `main.py:23-28` | `allow_origins=["*"]` 과도한 CORS |
| 8 | SAST | `app.js:14` | `innerHTML` XSS |
| 9 | Secrets | `extract.py:13` | 하드코딩된 API 토큰 |
| 10 | SCA | `requirements.txt` | 전 패키지 구버전 (CVE 다수) |
