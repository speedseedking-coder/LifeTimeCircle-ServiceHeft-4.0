from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.core.security import Actor, require_roles
from app.db.session import get_db
from app.schemas.masterclipboard import (
    SessionCreateRequest,
    SessionCreateResponse,
    SpeechChunkCreateRequest,
    SpeechChunkCreateResponse,
    TriageItemsCreateRequest,
    TriageItemsCreateResponse,
    TriageItemPatchRequest,
    OkResponse,
    BoardSnapshotCreateRequest,
    BoardSnapshotCreateResponse,
)
from app.services import masterclipboard as svc


router = APIRouter(prefix="/api/masterclipboard", tags=["masterclipboard"])


def _require_idempotency_key(idempotency_key: str | None) -> str:
    if not idempotency_key:
        # idempotency ist Pflicht für mutierende Calls
        raise ValueError("missing_idempotency_key")
    return idempotency_key


@router.post(
    "/sessions",
    response_model=SessionCreateResponse,
    status_code=201,
    dependencies=[rate_limit("mc_sessions_create", limit=30, window_seconds=60)],
)
def create_session(
    req: SessionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("dealer", "admin", "superadmin"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    try:
        ik = _require_idempotency_key(idempotency_key)
    except ValueError:
        return Response(status_code=400, content='{"error":"missing_idempotency_key"}', media_type="application/json")

    status, body = svc.create_session(db, actor, req.vehicle_public_id, ik)
    db.commit()
    return Response(status_code=status, content=SessionCreateResponse(**body).model_dump_json(), media_type="application/json")


@router.post(
    "/sessions/{session_id}/speech",
    response_model=SpeechChunkCreateResponse,
    status_code=201,
    dependencies=[rate_limit("mc_speech_add", limit=120, window_seconds=60)],
)
def add_speech(
    session_id: str,
    req: SpeechChunkCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("dealer", "admin", "superadmin"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    try:
        ik = _require_idempotency_key(idempotency_key)
    except ValueError:
        return Response(status_code=400, content='{"error":"missing_idempotency_key"}', media_type="application/json")

    status, body = svc.add_speech_chunk(db, actor, session_id, req.source, req.content_redacted, ik)
    db.commit()
    if status != 201:
        return Response(status_code=status, content=str(body).replace("'", '"'), media_type="application/json")
    return Response(status_code=status, content=SpeechChunkCreateResponse(**body).model_dump_json(), media_type="application/json")


@router.post(
    "/sessions/{session_id}/triage/items",
    response_model=TriageItemsCreateResponse,
    status_code=201,
    dependencies=[rate_limit("mc_triage_create", limit=60, window_seconds=60)],
)
def create_triage_items(
    session_id: str,
    req: TriageItemsCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("dealer", "admin", "superadmin"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    try:
        ik = _require_idempotency_key(idempotency_key)
    except ValueError:
        return Response(status_code=400, content='{"error":"missing_idempotency_key"}', media_type="application/json")

    items = [i.model_dump() for i in req.items]
    status, body = svc.create_triage_items(db, actor, session_id, items, ik)
    db.commit()
    if status != 201:
        return Response(status_code=status, content=str(body).replace("'", '"'), media_type="application/json")
    return Response(status_code=status, content=TriageItemsCreateResponse(**body).model_dump_json(), media_type="application/json")


@router.patch(
    "/sessions/{session_id}/triage/items/{item_id}",
    response_model=OkResponse,
    status_code=200,
    dependencies=[rate_limit("mc_triage_patch", limit=120, window_seconds=60)],
)
def patch_triage_item(
    session_id: str,
    item_id: str,
    req: TriageItemPatchRequest,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("dealer", "admin", "superadmin"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    try:
        ik = _require_idempotency_key(idempotency_key)
    except ValueError:
        return Response(status_code=400, content='{"error":"missing_idempotency_key"}', media_type="application/json")

    patch = {k: v for k, v in req.model_dump().items() if v is not None}
    status, body = svc.patch_triage_item(db, actor, session_id, item_id, patch, ik)
    db.commit()
    if status != 200:
        return Response(status_code=status, content=str(body).replace("'", '"'), media_type="application/json")
    return Response(status_code=status, content=OkResponse(**body).model_dump_json(), media_type="application/json")


@router.post(
    "/sessions/{session_id}/board/snapshot",
    response_model=BoardSnapshotCreateResponse,
    status_code=201,
    dependencies=[rate_limit("mc_board_snapshot", limit=60, window_seconds=60)],
)
def board_snapshot(
    session_id: str,
    req: BoardSnapshotCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("dealer", "admin", "superadmin"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    try:
        ik = _require_idempotency_key(idempotency_key)
    except ValueError:
        return Response(status_code=400, content='{"error":"missing_idempotency_key"}', media_type="application/json")

    status, body = svc.create_board_snapshot(db, actor, session_id, req.ordered_item_ids, req.notes_redacted, ik)
    db.commit()
    if status != 201:
        return Response(status_code=status, content=str(body).replace("'", '"'), media_type="application/json")
    return Response(status_code=status, content=BoardSnapshotCreateResponse(**body).model_dump_json(), media_type="application/json")


@router.post(
    "/sessions/{session_id}/close",
    response_model=OkResponse,
    status_code=200,
    dependencies=[rate_limit("mc_close", limit=60, window_seconds=60)],
)
def close_session(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[Actor, Depends(require_roles("dealer", "admin", "superadmin"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    try:
        ik = _require_idempotency_key(idempotency_key)
    except ValueError:
        return Response(status_code=400, content='{"error":"missing_idempotency_key"}', media_type="application/json")

    status, body = svc.close_session(db, actor, session_id, ik)
    db.commit()
    if status != 200:
        return Response(status_code=status, content=str(body).replace("'", '"'), media_type="application/json")
    return Response(status_code=status, content=OkResponse(**body).model_dump_json(), media_type="application/json")
