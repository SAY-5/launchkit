from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import TenantScope, get_scope
from app.models import Note
from app.schemas import NoteCreate, NoteResponse, SummarizeResponse
from app.services.provider import get_provider

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[NoteResponse])
def list_notes(scope: Annotated[TenantScope, Depends(get_scope)]) -> list[Note]:
    return scope.query(Note)


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreate, scope: Annotated[TenantScope, Depends(get_scope)]
) -> Note:
    return scope.add(Note(title=payload.title, body=payload.body))


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, scope: Annotated[TenantScope, Depends(get_scope)]) -> Note:
    note = scope.get_owned(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@router.post("/{note_id}/summarize", response_model=SummarizeResponse)
def summarize_note(
    note_id: int, scope: Annotated[TenantScope, Depends(get_scope)]
) -> SummarizeResponse:
    note = scope.get_owned(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    note.summary = get_provider().summarize(note.body or note.title)
    scope.session.commit()
    return SummarizeResponse(id=note.id, summary=note.summary)
