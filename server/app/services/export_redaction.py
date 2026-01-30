import datetime as dt
import hashlib
import hmac
import os
from typing import Any, Dict


def _require_secret_key() -> str:
    secret = os.environ.get("LTC_SECRET_KEY", "").strip()
    if not secret:
        raise RuntimeError("LTC_SECRET_KEY fehlt (ENV).")
    return secret


def _hmac_hex(secret: str, value: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _iso(ts: Any) -> Any:
    if isinstance(ts, dt.datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        return ts.astimezone(dt.timezone.utc).isoformat()
    return ts


def redact_vehicle_row(vehicle_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redacted default: keine Klartext-PII, keine Secrets.
    Minimal halten.
    """
    secret = _require_secret_key()

    out: Dict[str, Any] = {"_redacted": True}

    if "id" in vehicle_row:
        out["id"] = vehicle_row.get("id")

    if "created_at" in vehicle_row:
        out["created_at"] = _iso(vehicle_row.get("created_at"))

    vin = vehicle_row.get("vin")
    if vin:
        out["vin_hmac"] = _hmac_hex(secret, str(vin))

    # explizit NICHT rausgeben:
    # - vin (klartext)
    # - owner_email
    # - sonstige PII
    return out


def redact_masterclipboard_row(mc_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    MasterClipboard redacted:
    - keine Klartext-PII
    - kein Freitext/Transcript/Notes
    - minimaler Meta-Block
    """
    secret = _require_secret_key()

    out: Dict[str, Any] = {"_redacted": True}

    if "id" in mc_row:
        out["id"] = mc_row.get("id")

    # Vehicle-Public-ID lieber pseudonymisieren
    vpid = mc_row.get("vehicle_public_id") or mc_row.get("vehiclePublicId") or mc_row.get("vehicle_id")
    if vpid:
        out["vehicle_public_id_hmac"] = _hmac_hex(secret, str(vpid))

    # status falls vorhanden
    for k in ("status", "state"):
        if k in mc_row and mc_row.get(k) is not None:
            out["status"] = mc_row.get(k)
            break

    # timestamps falls vorhanden
    for k in ("created_at", "createdAt"):
        if k in mc_row and mc_row.get(k) is not None:
            out["created_at"] = _iso(mc_row.get(k))
            break

    return out
