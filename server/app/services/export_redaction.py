import hmac
import hashlib
import os
from typing import Any, Dict, Mapping


_PII_KEYS_SUBSTR = (
    "email",
    "phone",
    "tel",
    "mobile",
    "name",
    "firstname",
    "lastname",
    "address",
    "street",
    "zip",
    "postal",
    "city",
    "country",
    "iban",
    "holder",
    "owner",
    "person",
    "birth",
    "dob",
)

_SECRET_KEYS_SUBSTR = (
    "secret",
    "token",
    "otp",
    "password",
    "access_key",
    "refresh",
)


def _require_secret_key() -> str:
    secret = os.environ.get("LTC_SECRET_KEY", "").strip()
    if not secret:
        raise RuntimeError("LTC_SECRET_KEY fehlt (ENV).")
    return secret


def _hmac_hex(secret: str, value: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _is_sensitive_key(key: str) -> bool:
    k = key.lower()
    if any(s in k for s in _SECRET_KEYS_SUBSTR):
        return True
    if any(s in k for s in _PII_KEYS_SUBSTR):
        return True
    return False


def redact_vehicle_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Redacted default:
    - keine Klartext-PII
    - keine Secrets/Tokens/OTPs
    - VIN (falls vorhanden) wird zu vin_hmac pseudonymisiert und entfernt
    """
    secret = _require_secret_key()
    out: Dict[str, Any] = {}

    # Baseline: alles raus, was offensichtlich PII/Secrets ist
    for k, v in dict(row).items():
        if v is None:
            continue
        if _is_sensitive_key(k):
            continue
        out[k] = v

    # VIN Sonderfall (häufig kein PII, aber eindeutig + policy-sicherer über HMAC)
    vin = None
    for vin_key in ("vin", "VIN"):
        if vin_key in row and row[vin_key]:
            vin = str(row[vin_key])
            break
    if vin:
        out.pop("vin", None)
        out.pop("VIN", None)
        out["vin_hmac"] = _hmac_hex(secret, vin)

    # Marker
    out["_redacted"] = True
    return out
