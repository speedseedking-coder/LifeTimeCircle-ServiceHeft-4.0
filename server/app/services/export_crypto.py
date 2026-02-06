import base64
import datetime as dt
import hashlib
import json
import os
from typing import Any, Dict

from cryptography.fernet import Fernet, InvalidToken


def _require_secret_key() -> str:
    secret = os.environ.get("LTC_SECRET_KEY", "").strip()
    if not secret:
        raise RuntimeError("LTC_SECRET_KEY fehlt (ENV).")
    return secret


def _fernet_from_secret(secret: str) -> Fernet:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()  # 32 bytes
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def _json_default(o: Any) -> Any:
    # datetime/date -> ISO 8601
    if isinstance(o, (dt.datetime, dt.date)):
        if isinstance(o, dt.datetime):
            # wenn naive -> als UTC interpretieren
            if o.tzinfo is None:
                o = o.replace(tzinfo=dt.timezone.utc)
            return o.astimezone(dt.timezone.utc).isoformat()
        return o.isoformat()

    # Fallback: niemals crashen, aber bewusst als String
    return str(o)


def encrypt_json(payload: Dict[str, Any]) -> str:
    secret = _require_secret_key()
    f = _fernet_from_secret(secret)
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_json_default,
    ).encode("utf-8")
    return f.encrypt(raw).decode("utf-8")


def decrypt_json(ciphertext: str) -> Dict[str, Any]:
    secret = _require_secret_key()
    f = _fernet_from_secret(secret)
    try:
        raw = f.decrypt(ciphertext.encode("utf-8"))
    except InvalidToken as e:
        raise ValueError("ciphertext ungültig") from e
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("payload ist kein JSON-Objekt")
    return obj
