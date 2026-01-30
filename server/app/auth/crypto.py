from __future__ import annotations

import base64
import hmac
import os
import secrets
import unicodedata
from hashlib import sha256


def normalize_email(email: str) -> str:
    # Policy: trim + lowercase + Unicode NFKC
    return unicodedata.normalize("NFKC", email.strip().lower())


def hmac_sha256_base64url(secret_key: str, value: str) -> str:
    mac = hmac.new(secret_key.encode("utf-8"), value.encode("utf-8"), sha256).digest()
    return base64.urlsafe_b64encode(mac).decode("utf-8").rstrip("=")


def email_hmac(secret_key: str, email: str) -> str:
    return hmac_sha256_base64url(secret_key, normalize_email(email))


def ip_hmac(secret_key: str, ip: str) -> str:
    return hmac_sha256_base64url(secret_key, f"ip:{ip.strip()}")


def ua_hmac(secret_key: str, ua: str) -> str:
    return hmac_sha256_base64url(secret_key, f"ua:{ua.strip()}")


def otp_hash(secret_key: str, otp: str, challenge_id: str) -> str:
    # Policy: otp_hash = HMAC(secret, otp + challenge_id)
    return hmac_sha256_base64url(secret_key, f"{otp}{challenge_id}")


def token_hash(secret_key: str, raw_token: str) -> str:
    # Policy: token_hash = HMAC(secret, raw_token)
    return hmac_sha256_base64url(secret_key, raw_token)


def new_otp() -> str:
    # 6-stellig, ohne führende Null-Probleme
    return f"{secrets.randbelow(1_000_000):06d}"


def new_session_token() -> str:
    # URL-safe random token
    return secrets.token_urlsafe(32)


def ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
