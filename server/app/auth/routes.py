from __future__ import annotations

import uuid
from fastapi import APIRouter, Request, HTTPException, status, Depends

from .schemas import AuthRequestIn, AuthRequestOut, AuthVerifyIn, AuthVerifyOut, MeOut, LogoutOut
from .service import request_challenge, verify_challenge_and_create_session, logout
from .settings import load_settings
from .deps import require_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _request_id(request: Request) -> str:
    rid = request.headers.get("x-request-id") or request.headers.get("x-correlation-id")
    return rid.strip() if rid and rid.strip() else str(uuid.uuid4())


def _client_ip(request: Request) -> str:
    # reverse proxy später: X-Forwarded-For sauber verarbeiten
    return request.client.host if request.client else "0.0.0.0"


def _bearer_token_from_header(request: Request) -> str:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    return parts[1].strip()


@router.post("/request", response_model=AuthRequestOut)
def auth_request(body: AuthRequestIn, request: Request) -> AuthRequestOut:
    settings = load_settings()
    rid = _request_id(request)

    challenge_id, dev_otp = request_challenge(
        settings,
        email=body.email,
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
        request_id=rid,
    )

    # Anti-Enumeration: immer gleich
    msg = "Wenn die E-Mail-Adresse gültig ist, wurde ein Code gesendet."
    return AuthRequestOut(ok=True, challenge_id=challenge_id, message=msg, dev_otp=dev_otp)


@router.post("/verify", response_model=AuthVerifyOut)
def auth_verify(body: AuthVerifyIn, request: Request) -> AuthVerifyOut:
    settings = load_settings()
    rid = _request_id(request)

    try:
        token, expires_at = verify_challenge_and_create_session(
            settings,
            email=body.email,
            challenge_id=body.challenge_id,
            otp=body.otp,
            ip=_client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
            request_id=rid,
        )
        return AuthVerifyOut(access_token=token, expires_at=expires_at)

    except ValueError as e:
        code = str(e)

        if code == "RATE_LIMIT":
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="RATE_LIMIT")
        if code == "EXPIRED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EXPIRED")
        if code == "LOCKED":
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="LOCKED")

        # default: INVALID (keine Details)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID")


@router.get("/me", response_model=MeOut)
def me(user=Depends(require_user)) -> MeOut:
    return MeOut(user_id=user["user_id"], role=user["role"])


@router.post("/logout", response_model=LogoutOut)
def do_logout(request: Request, user=Depends(require_user)) -> LogoutOut:
    settings = load_settings()
    rid = _request_id(request)

    # robust: token entweder aus require_user oder aus Authorization Header
    raw_token = None
    if isinstance(user, dict):
        raw_token = user.get("token")

    if not raw_token:
        raw_token = _bearer_token_from_header(request)

    logout(settings, raw_token, request_id=rid)
    return LogoutOut(ok=True)


# --- Consent endpoints: AGB + Datenschutz Pflicht (Version + Timestamp) ---
# Speichert Version + Timestamp auditierbar. Keine PII / Tokens im Klartext loggen.
from fastapi import Body, Depends, HTTPException
from app.consent_store import record_consent, get_consent_status, env_consent_version, env_db_path
from app.rbac import get_current_user

def _ltc_uid(u):
    if u is None:
        return None
    if isinstance(u, dict):
        return u.get("user_id") or u.get("id") or u.get("uid")
    return getattr(u, "user_id", None) or getattr(u, "id", None) or getattr(u, "uid", None)

@router.get("/consent")
def consent_status(user = Depends(get_current_user)):
    uid = _ltc_uid(user)
    if uid is None:
        raise HTTPException(status_code=401, detail={"code": "unauthenticated"})
    required_version = env_consent_version()
    st = get_consent_status(env_db_path(), str(uid), required_version)
    return {
        "required_version": st.required_version,
        "has_required": st.has_required,
        "latest_version": st.latest_version,
        "latest_accepted_at": st.latest_accepted_at,
        "latest_source": st.latest_source,
    }

@router.post("/consent")
def accept_consent(payload: dict = Body(...), user = Depends(get_current_user)):
    uid = _ltc_uid(user)
    if uid is None:
        raise HTTPException(status_code=401, detail={"code": "unauthenticated"})

    agb = bool(payload.get("agb"))
    ds = bool(payload.get("datenschutz"))
    if not (agb and ds):
        raise HTTPException(status_code=400, detail={"code": "consent_required", "consent_version": env_consent_version()})

    source = payload.get("source", "web")
    version = env_consent_version()
    accepted_at = record_consent(env_db_path(), str(uid), version, str(source))
    return {"ok": True, "consent_version": version, "accepted_at": accepted_at}
