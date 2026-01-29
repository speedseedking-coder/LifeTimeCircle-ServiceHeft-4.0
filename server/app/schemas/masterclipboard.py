from typing import Literal

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    vehicle_public_id: str = Field(min_length=1, max_length=64)


class SessionCreateResponse(BaseModel):
    session_id: str


class SpeechChunkCreateRequest(BaseModel):
    source: Literal["mic", "text"]
    content_redacted: str = Field(min_length=1, max_length=20_000)


class SpeechChunkCreateResponse(BaseModel):
    speech_chunk_id: str


class TriageItemIn(BaseModel):
    kind: Literal["defect", "task", "recommendation"]
    title: str = Field(min_length=1, max_length=160)
    details_redacted: str | None = Field(default=None, max_length=20_000)
    severity: Literal["low", "medium", "high"]
    status: Literal["open", "in_progress", "done", "blocked"]
    evidence_refs: list[str] | None = None


class TriageItemsCreateRequest(BaseModel):
    items: list[TriageItemIn] = Field(min_length=1, max_length=200)


class TriageItemsCreateResponse(BaseModel):
    created_ids: list[str]


class TriageItemPatchRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    details_redacted: str | None = Field(default=None, max_length=20_000)
    severity: Literal["low", "medium", "high"] | None = None
    status: Literal["open", "in_progress", "done", "blocked"] | None = None


class OkResponse(BaseModel):
    ok: bool = True


class BoardSnapshotCreateRequest(BaseModel):
    ordered_item_ids: list[str] = Field(min_length=0, max_length=500)
    notes_redacted: str | None = Field(default=None, max_length=20_000)


class BoardSnapshotCreateResponse(BaseModel):
    snapshot_id: str
