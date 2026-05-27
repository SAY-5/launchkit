from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import TenantScope, get_scope
from app.models import Note
from app.schemas import NoteCreate, NoteResponse, NoteUpdate, SummarizeResponse
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
    return scope.require_owned(Note, note_id)


@router.patch("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int, payload: NoteUpdate, scope: Annotated[TenantScope, Depends(get_scope)]
) -> Note:
    note = scope.require_owned(Note, note_id)
    if payload.title is not None:
        note.title = payload.title
    if payload.body is not None:
        note.body = payload.body
    return scope.save(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, scope: Annotated[TenantScope, Depends(get_scope)]) -> None:
    note = scope.require_owned(Note, note_id)
    scope.session.delete(note)
    scope.session.commit()


@router.post("/{note_id}/summarize", response_model=SummarizeResponse)
def summarize_note(
    note_id: int, scope: Annotated[TenantScope, Depends(get_scope)]
) -> SummarizeResponse:
    note = scope.require_owned(Note, note_id)
    note.summary = get_provider().summarize(note.body or note.title)
    scope.save(note)
    return SummarizeResponse(id=note.id, summary=note.summary or "")
