from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from .audit import write_audit
from .crypto import (
    email_hmac as email_hmac_fn,
    ip_hmac as ip_hmac_fn,
    ua_hmac as ua_hmac_fn,
    new_otp,
    new_session_token,
    otp_hash as otp_hash_fn,
    token_hash as token_hash_fn,
)
from .mailer import get_mailer
from .rate_limit import check_and_inc
from .settings import AuthSettings
from .storage import (
    init_db,
    db,
    upsert_user,
    get_user_by_email_hmac,
    insert_challenge,
    get_challenge,
    mark_challenge_attempt,
    mark_challenge_used,
    insert_session,
    get_session_by_token_hash,
    revoke_session,
    insert_consent,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def request_challenge(
    settings: AuthSettings,
    *,
    email: str,
    ip: str,
    user_agent: str,
    request_id: str,
) -> Tuple[str, Optional[str]]:
    """
    Anti-Enumeration: immer gleiche Antwort.
    OTP wird NICHT geloggt und NICHT persistiert.
    Versand erfolgt über Mailer (null|smtp). In dev optional dev_otp response.
    """
    init_db(settings.db_path)

    e_h = email_hmac_fn(settings.secret_key, email)
    ip_h = ip_hmac_fn(settings.secret_key, ip)
    ua_h = ua_hmac_fn(settings.secret_key, user_agent)

    with db(settings.db_path) as conn:
        # Rate limits (request)
        if not check_and_inc(conn, f"rl:req:email:{e_h}", settings.rl_window_seconds, settings.rl_req_per_email):
            write_audit(
                conn,
                actor_id="public",
                actor_role="public",
                action="AUTH_CHALLENGE_CREATED",
                target_type="USER",
                target_id=None,
                scope="public",
                result="denied",
                request_id=request_id,
                reason_code="RATE_LIMIT",
                redacted_metadata={"kind": "auth_request", "key": "email"},
            )
            return (str(uuid.uuid4()), None)

        if not check_and_inc(conn, f"rl:req:ip:{ip_h}", settings.rl_window_seconds, settings.rl_req_per_ip):
            write_audit(
                conn,
                actor_id="public",
                actor_role="public",
                action="AUTH_CHALLENGE_CREATED",
                target_type="USER",
                target_id=None,
                scope="public",
                result="denied",
                request_id=request_id,
                reason_code="RATE_LIMIT",
                redacted_metadata={"kind": "auth_request", "key": "ip"},
            )
            return (str(uuid.uuid4()), None)

        # user upsert (ohne Klartext-Email)
        user_row = get_user_by_email_hmac(conn, e_h)
        if user_row is None:
            user_id = str(uuid.uuid4())
            upsert_user(conn, user_id=user_id, email_hmac=e_h, created_at=_iso(_utc_now()))
        else:
            user_id = user_row["user_id"]

        # challenge
        challenge_id = str(uuid.uuid4())
        otp = new_otp()
        otp_hash = otp_hash_fn(settings.secret_key, otp, challenge_id)

        now = _utc_now()
        expires = now + timedelta(seconds=settings.otp_ttl_seconds)

        insert_challenge(
            conn,
            challenge_id=challenge_id,
            email_hmac=e_h,
            otp_hash=otp_hash,
            created_at=_iso(now),
            expires_at=_iso(expires),
        )

        write_audit(
            conn,
            actor_id="public",
            actor_role="public",
            action="AUTH_CHALLENGE_CREATED",
            target_type="USER",
            target_id=user_id,
            scope="public",
            result="success",
            request_id=request_id,
            redacted_metadata={"kind": "auth_request"},
        )

    # Versand NACH DB-Commit (kein DB-Lock, keine PII/OTP Logs)
    try:
        mailer = get_mailer(settings)
        mailer.send_login_otp(to_email=email, otp=otp, challenge_id=challenge_id)

        with db(settings.db_path) as conn2:
            write_audit(
                conn2,
                actor_id="public",
                actor_role="public",
                action="AUTH_CHALLENGE_DELIVERED",
                target_type="USER",
                target_id=user_id,
                scope="public",
                result="success",
                request_id=request_id,
                redacted_metadata={"kind": "auth_delivery"},
            )
    except Exception:
        # Keine Details loggen/ausgeben (keine Secrets/PII).
        with db(settings.db_path) as conn3:
            write_audit(
                conn3,
                actor_id="public",
                actor_role="public",
                action="AUTH_CHALLENGE_DELIVERY_FAILED",
                target_type="USER",
                target_id=user_id,
                scope="public",
                result="error",
                request_id=request_id,
                redacted_metadata={"kind": "auth_delivery"},
            )

    dev_otp = otp if settings.dev_expose_otp else None
    return (challenge_id, dev_otp)


def verify_challenge_and_create_session(
    settings: AuthSettings,
    *,
    email: str,
    challenge_id: str,
    otp: str,
    consents: list[dict],
    ip: str,
    user_agent: str,
    request_id: str,
) -> Tuple[str, str]:
    """
    Verify OTP (HMAC), enforce TTL + rate limits,
    enforce consent versions (AGB+Datenschutz Pflicht, serverseitig).
    """
    init_db(settings.db_path)

    e_h = email_hmac_fn(settings.secret_key, email)
    ip_h = ip_hmac_fn(settings.secret_key, ip)
    ua_h = ua_hmac_fn(settings.secret_key, user_agent)

    with db(settings.db_path) as conn:
        # rate limit verify by ip
        if not check_and_inc(conn, f"rl:verify:ip:{ip_h}", settings.rl_window_seconds, settings.rl_verify_per_ip):
            write_audit(
                conn,
                actor_id="public",
                actor_role="public",
                action="AUTH_CHALLENGE_VERIFIED",
                target_type="USER",
                target_id=None,
                scope="public",
                result="denied",
                request_id=request_id,
                reason_code="RATE_LIMIT",
                redacted_metadata={"kind": "auth_verify", "key": "ip"},
            )
            raise ValueError("RATE_LIMIT")

        user_row = get_user_by_email_hmac(conn, e_h)
        if user_row is None:
            write_audit(
                conn,
                actor_id="public",
                actor_role="public",
                action="AUTH_CHALLENGE_VERIFIED",
                target_type="USER",
                target_id=None,
                scope="public",
                result="denied",
                reason_code="RBAC_DENY",
                request_id=request_id,
                redacted_metadata={"kind": "auth_verify", "reason": "user_missing"},
            )
            raise ValueError("INVALID")

        user_id = user_row["user_id"]
        role = user_row["role"]

        ch = get_challenge(conn, challenge_id)
        if ch is None or ch["email_hmac"] != e_h:
            write_audit(
                conn,
                actor_id="public",
                actor_role="public",
                action="AUTH_CHALLENGE_VERIFIED",
                target_type="USER",
                target_id=user_id,
                scope="public",
                result="denied",
                reason_code="RBAC_DENY",
                request_id=request_id,
                redacted_metadata={"kind": "auth_verify", "reason": "challenge_mismatch"},
            )
            raise ValueError("INVALID")

        if ch["used_at"] is not None:
            raise ValueError("INVALID")

        now = _utc_now()
        expires_at = datetime.fromisoformat(ch["expires_at"])
        if now > expires_at:
            write_audit(
                conn,
                actor_id=user_id,
                actor_role=role,
                action="AUTH_CHALLENGE_VERIFIED",
                target_type="USER",
                target_id=user_id,
                scope="own",
                result="denied",
                reason_code="RBAC_DENY",
                request_id=request_id,
                redacted_metadata={"kind": "auth_verify", "reason": "expired"},
            )
            raise ValueError("EXPIRED")

        attempts = int(ch["attempts"])
        if attempts >= 5:
            raise ValueError("LOCKED")

        expected = otp_hash_fn(settings.secret_key, otp, challenge_id)
        if expected != ch["otp_hash"]:
            attempts += 1
            mark_challenge_attempt(conn, challenge_id, attempts, _iso(now))
            write_audit(
                conn,
                actor_id=user_id,
                actor_role=role,
                action="AUTH_CHALLENGE_FAILED",
                target_type="USER",
                target_id=user_id,
                scope="own",
                result="denied",
                reason_code="RBAC_DENY",
                request_id=request_id,
                redacted_metadata={"kind": "auth_verify", "reason": "otp_invalid"},
            )
            raise ValueError("INVALID")

        # --- CONSENT GATE (Versionen serverseitig enforced) ---
        req_terms = settings.terms_version_required
        req_privacy = settings.privacy_version_required

        terms_ok = any(
            (c.get("doc_type") == "terms" and c.get("doc_version") == req_terms)
            for c in consents
        )
        privacy_ok = any(
            (c.get("doc_type") == "privacy" and c.get("doc_version") == req_privacy)
            for c in consents
        )

        if not (terms_ok and privacy_ok):
            has_terms_any = any(c.get("doc_type") == "terms" for c in consents)
            has_privacy_any = any(c.get("doc_type") == "privacy" for c in consents)

            if not (has_terms_any and has_privacy_any):
                reason = "CONSENT_MISSING"
            else:
                reason = "CONSENT_VERSION_MISMATCH"

            write_audit(
                conn,
                actor_id=user_id,
                actor_role=role,
                action="CONSENT_REQUIRED_BLOCK",
                target_type="USER",
                target_id=user_id,
                scope="own",
                result="denied",
                reason_code=reason,
                request_id=request_id,
                redacted_metadata={
                    "kind": "consent_gate",
                    "terms_required": req_terms,
                    "privacy_required": req_privacy,
                },
            )
            raise ValueError("CONSENT_REQUIRED")

        # store consents (ohne Klartext-PII)
        for c in consents:
            insert_consent(
                conn,
                user_id=user_id,
                doc_type=c["doc_type"],
                doc_version=c["doc_version"],
                accepted_at=c["accepted_at"],
                source=c.get("source", "ui"),
                ip_hmac=ip_h,
                ua_hmac=ua_h,
                evidence_hash=c.get("evidence_hash"),
            )

        mark_challenge_used(conn, challenge_id, _iso(now))

        # create session token
        raw_token = new_session_token()
        th = token_hash_fn(settings.secret_key, raw_token)
        session_id = str(uuid.uuid4())
        sess_expires = now + timedelta(seconds=settings.session_ttl_seconds)

        insert_session(
            conn,
            session_id=session_id,
            user_id=user_id,
            token_hash=th,
            created_at=_iso(now),
            expires_at=_iso(sess_expires),
        )

        write_audit(
            conn,
            actor_id=user_id,
            actor_role=role,
            action="SESSION_CREATED",
            target_type="USER",
            target_id=user_id,
            scope="own",
            result="success",
            request_id=request_id,
            redacted_metadata={"kind": "session_created"},
        )

        return raw_token, _iso(sess_expires)
def resolve_me(settings: AuthSettings, raw_token: str) -> Optional[Tuple[str, str]]:
    init_db(settings.db_path)

    # Token wird nur gehasht verwendet (kein Klartext im Storage/Logs)
    th = token_hash_fn(settings.secret_key, raw_token)

    with db(settings.db_path) as conn:
        sess = get_session_by_token_hash(conn, th)
        if sess is None:
            return None

        now = _utc_now()
        exp = datetime.fromisoformat(sess["expires_at"])
        if now > exp:
            return None

        user_id = sess["user_id"]
        user = conn.execute("SELECT * FROM auth_users WHERE user_id = ? LIMIT 1;", (user_id,)).fetchone()
        if user is None:
            return None

        return (user["user_id"], user["role"])


def logout(settings: AuthSettings, raw_token: str, request_id: str) -> None:
    init_db(settings.db_path)

    th = token_hash_fn(settings.secret_key, raw_token)
    now = _iso(_utc_now())

    with db(settings.db_path) as conn:
        sess = get_session_by_token_hash(conn, th)
        if sess is None:
            return

        revoke_session(conn, th, now)
        write_audit(
            conn,
            actor_id=sess["user_id"],
            actor_role="user",
            action="SESSION_REVOKED",
            target_type="USER",
            target_id=sess["user_id"],
            scope="own",
            result="success",
            request_id=request_id,
            redacted_metadata={"kind": "logout"},
        )

