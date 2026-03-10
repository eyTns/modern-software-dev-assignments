from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# ── Logging (stderr only — stdout is reserved for STDIO transport) ──

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("varchive-mcp")

# ── Constants ──

VARCHIVE_API_BASE = "https://v-archive.net"
SONGS_JSON_URL = f"{VARCHIVE_API_BASE}/db/songs.json"
SONGS_CACHE_PATH = Path(__file__).parent / "songs.json"
CACHE_MAX_AGE_DAYS = 5
VALID_BUTTONS = {4, 5, 6, 8}
REQUEST_TIMEOUT = 30.0

# ── FastMCP server ──

mcp = FastMCP("varchive", instructions="DJMAX Respect V player records via V-Archive")

# ── HTTP helper ──


async def make_varchive_request(url: str) -> dict[str, Any]:
    """V-Archive API에 요청을 보내고 JSON 응답을 반환한다.

    성공 시 파싱된 dict를, 실패 시 {"success": False, "message": ...} 형태를 반환한다.
    """
    headers = {"Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        except httpx.TimeoutException:
            logger.warning("Request timed out: %s", url)
            return {"success": False, "message": "요청 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."}
        except httpx.ConnectError:
            logger.warning("Connection failed: %s", url)
            return {"success": False, "message": "V-Archive 서버에 연결할 수 없습니다."}

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "잠시")
            logger.warning("Rate limited. Retry-After: %s", retry_after)
            return {
                "success": False,
                "message": f"API 요청 한도를 초과했습니다. {retry_after}초 후 다시 시도해 주세요.",
            }

        try:
            data = response.json()
        except Exception:
            logger.error("Invalid JSON from %s (HTTP %d)", url, response.status_code)
            return {"success": False, "message": f"서버 응답을 해석할 수 없습니다 (HTTP {response.status_code})."}

        if response.status_code >= 400:
            error_code = data.get("errorCode", "")
            msg = data.get("message", f"HTTP {response.status_code}")
            logger.warning("API error %s: %s", error_code, msg)
            return {"success": False, "message": msg}

        return data


# ── Song cache ──


def _cache_is_stale() -> bool:
    if not SONGS_CACHE_PATH.exists():
        return True
    age_seconds = time.time() - SONGS_CACHE_PATH.stat().st_mtime
    return age_seconds > CACHE_MAX_AGE_DAYS * 86400


async def _download_songs() -> list[dict[str, Any]]:
    """songs.json을 다운로드하여 로컬 캐시에 저장한다."""
    logger.info("Downloading songs.json from V-Archive...")
    async with httpx.AsyncClient() as client:
        response = await client.get(SONGS_JSON_URL, timeout=60.0)
        response.raise_for_status()
        songs = response.json()
    SONGS_CACHE_PATH.write_text(json.dumps(songs, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved %d songs to cache.", len(songs))
    return songs


async def load_songs() -> list[dict[str, Any]]:
    """로컬 캐시에서 곡 목록을 로드한다. 캐시가 없거나 오래되면 자동 갱신한다."""
    if _cache_is_stale():
        return await _download_songs()
    text = SONGS_CACHE_PATH.read_text(encoding="utf-8")
    return json.loads(text)


# ── Tool 1: get_user_tier ──


@mcp.tool()
async def get_user_tier(nickname: str, button: int) -> str:
    """Get a DJMAX Respect V user's tier ranking from V-Archive.

    Args:
        nickname: V-Archive nickname of the player
        button: Button mode (4, 5, 6, or 8)
    """
    if button not in VALID_BUTTONS:
        return f"잘못된 버튼 값입니다: {button}. 4, 5, 6, 8 중 하나를 선택해 주세요."

    url = f"{VARCHIVE_API_BASE}/api/archive/{nickname}/tier/{button}"
    data = await make_varchive_request(url)

    if not data.get("success", False):
        return data.get("message", "티어 정보를 가져올 수 없습니다.")

    tier = data.get("tier", {})
    next_tier = data.get("next", {})
    tier_point = data.get("tierPoint", 0)
    top50sum = data.get("top50sum", 0)

    lines = [
        f"[{nickname}] {button}B 티어 정보",
        f"  현재 티어: {tier.get('name', '?')} ({tier.get('code', '?')})",
        f"  티어 포인트: {tier_point:,.2f}",
        f"  상위 50곡 합산: {top50sum:,.4f}",
    ]

    if next_tier:
        gap = next_tier.get("rating", 0) - tier_point
        lines.append(f"  다음 티어: {next_tier.get('name', '?')} (필요 포인트: {gap:,.2f})")

    top_list = data.get("topList", [])
    if top_list:
        lines.append(f"\n  상위 곡 (총 {len(top_list)}곡 중 상위 5곡):")
        for i, entry in enumerate(top_list[:5], 1):
            name = entry.get("name", "?")
            pattern = entry.get("pattern", "?")
            level = entry.get("level", "?")
            score = entry.get("score", "?")
            rating = entry.get("rating", "?")
            lines.append(f"    {i}. {name} [{button}B {pattern} Lv.{level}] — {score}% (rating {rating})")

    return "\n".join(lines)


# ── Tool 2: get_user_song_record ──


def _format_patterns(patterns: dict[str, Any]) -> list[str]:
    """패턴 데이터를 읽기 좋은 문자열 목록으로 변환한다."""
    lines: list[str] = []
    for btn in ("4B", "5B", "6B", "8B"):
        btn_data = patterns.get(btn)
        if not btn_data:
            continue
        for diff in ("NM", "HD", "MX", "SC"):
            p = btn_data.get(diff)
            if not p:
                continue
            level = p.get("level", "?")
            score = p.get("score")
            if score is None:
                lines.append(f"  {btn} {diff} Lv.{level} — 기록 없음")
            else:
                max_combo = "MAX COMBO" if p.get("maxCombo") == 1 else ""
                rating = p.get("rating", "")
                djpower = p.get("djpower", "")
                parts = [f"  {btn} {diff} Lv.{level} — {score}%"]
                if max_combo:
                    parts.append(max_combo)
                if rating:
                    parts.append(f"rating {rating}")
                if djpower:
                    parts.append(f"DJ Power {djpower}")
                lines.append(" | ".join(parts))
    return lines


@mcp.tool()
async def get_user_song_record(nickname: str, title_num: int) -> str:
    """Get a DJMAX Respect V user's record for a specific song from V-Archive.

    Args:
        nickname: V-Archive nickname of the player
        title_num: Song ID number (use search_songs to find this)
    """
    url = f"{VARCHIVE_API_BASE}/api/archive/{nickname}/title/{title_num}"
    data = await make_varchive_request(url)

    if not data.get("success", False):
        return data.get("message", "곡 기록을 가져올 수 없습니다.")

    song_name = data.get("name", "?")
    composer = data.get("composer", "?")
    dlc = data.get("dlc", "?")
    patterns = data.get("patterns", {})

    lines = [
        f"[{nickname}] {song_name}",
        f"  작곡: {composer}",
        f"  DLC: {dlc}",
        "",
    ]

    pattern_lines = _format_patterns(patterns)
    if pattern_lines:
        lines.extend(pattern_lines)
    else:
        lines.append("  기록이 없습니다.")

    return "\n".join(lines)


# ── Tool 3: search_songs ──


@mcp.tool()
async def search_songs(query: str) -> str:
    """Search DJMAX Respect V songs by name. Returns matching song IDs and names.

    Args:
        query: Song name to search for (partial match, case-insensitive)
    """
    songs = await load_songs()
    query_lower = query.lower()

    matches: list[dict[str, Any]] = []
    for song in songs:
        name: str = song.get("name", "")
        if query_lower in name.lower():
            matches.append(song)

    if not matches:
        return f"'{query}'에 해당하는 곡을 찾을 수 없습니다."

    total = len(matches)
    lines = [f"검색 결과: '{query}' ({total}건{', 상위 10건 표시' if total > 10 else ''})"]
    for song in matches[:10]:
        title = song.get("title", "?")
        name = song.get("name", "?")
        composer = song.get("composer", "?")
        dlc = song.get("dlc", "?")
        lines.append(f"  [{title}] {name} — {composer} ({dlc})")

    return "\n".join(lines)


# ── Tool 4: refresh_songs ──


@mcp.tool()
async def refresh_songs() -> str:
    """Force refresh the local DJMAX Respect V song database cache."""
    try:
        songs = await _download_songs()
        return f"곡 목록을 갱신했습니다. 총 {len(songs)}곡이 저장되었습니다."
    except Exception as e:
        logger.error("Failed to refresh songs: %s", e)
        return f"곡 목록 갱신에 실패했습니다: {e}"


# ── Entry point ──


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
