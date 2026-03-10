from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ActionItem, Note
from ..schemas import (
    ActionItemRead,
    ExtractedData,
    ExtractionResultSchema,
    NoteCreate,
    NoteRead,
    PaginatedResponse,
    SuccessResponse,
)
from ..services.extract import extract_all

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/")
def list_notes(page: int = 1, page_size: int = 10, db: Session = Depends(get_db)) -> dict:
    # Get total count
    total = db.scalar(select(func.count()).select_from(Note)) or 0

    # Calculate offset
    offset = (page - 1) * page_size

    # Query with pagination
    rows = db.execute(select(Note).offset(offset).limit(page_size)).scalars().all()

    paginated = PaginatedResponse(
        items=[NoteRead.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
    return SuccessResponse(data=paginated).model_dump()


@router.post("/", status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> dict:
    note = Note(title=payload.title, content=payload.content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return SuccessResponse(data=NoteRead.model_validate(note)).model_dump()


@router.get("/search/")
def search_notes(q: Optional[str] = None, db: Session = Depends(get_db)) -> dict:
    if not q:
        rows = db.execute(select(Note)).scalars().all()
    else:
        rows = (
            db.execute(select(Note).where((Note.title.contains(q)) | (Note.content.contains(q))))
            .scalars()
            .all()
        )
    return SuccessResponse(data=[NoteRead.model_validate(row) for row in rows]).model_dump()


@router.get("/{note_id}")
def get_note(note_id: int, db: Session = Depends(get_db)) -> dict:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return SuccessResponse(data=NoteRead.model_validate(note)).model_dump()


@router.post("/{note_id}/extract")
def extract_from_note(note_id: int, apply: bool = False, db: Session = Depends(get_db)) -> dict:
    """Extract hashtags and action items from a note.

    Args:
        note_id: ID of the note to extract from
        apply: If True, persist extracted action items to database
        db: Database session

    Returns:
        Extraction results with optional persistence confirmation
    """
    # Get the note
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Extract content
    extraction = extract_all(note.content)

    # If apply=False, just return extraction results
    if not apply:
        result = ExtractionResultSchema(
            hashtags=extraction["hashtags"], action_items=extraction["action_items"]
        )
        return SuccessResponse(data=result).model_dump()

    # If apply=True, persist action items
    created_items = []
    for item_description in extraction["action_items"]:
        # Check if similar action item already exists to avoid duplicates
        existing = db.execute(
            select(ActionItem).where(ActionItem.description == item_description)
        ).scalar_one_or_none()

        if not existing:
            action_item = ActionItem(description=item_description, completed=False)
            db.add(action_item)
            db.flush()
            db.refresh(action_item)
            created_items.append(ActionItemRead.model_validate(action_item))

    db.commit()

    # Return persisted data
    result = ExtractedData(action_items_created=created_items, tags_found=extraction["hashtags"])
    return SuccessResponse(data=result).model_dump()
