from __future__ import annotations

from pydantic import BaseModel


# ── Notes ──

class NoteCreateRequest(BaseModel):
    content: str


class NoteResponse(BaseModel):
    id: int
    content: str
    created_at: str


# ── Action Items ──

class ExtractRequest(BaseModel):
    text: str
    save_note: bool = False


class ActionItemOut(BaseModel):
    id: int
    text: str


class ExtractResponse(BaseModel):
    note_id: int | None
    items: list[ActionItemOut]


class ActionItemDetail(BaseModel):
    id: int
    note_id: int | None
    text: str
    done: bool
    created_at: str


class MarkDoneRequest(BaseModel):
    done: bool = True


class MarkDoneResponse(BaseModel):
    id: int
    done: bool
