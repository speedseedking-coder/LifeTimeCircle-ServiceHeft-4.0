import datetime as dt
import hmac
from hashlib import sha256
from typing import Any, Dict, Optional

from app.core.config import get_settings


_TEXT_KEYS = {
    "notes",
    "note",
    "description",
    "desc",
    "comment",
    "comments",
    "text",
    "free_text",
    "workshop_name",
    "workshop_address",
    "workshop_phone",
    "address",
    "phone",
    "email",
}


def _to_iso(v: Any) -> Any:
    if isinstance(v, dt.datetime):
        if v.tzinfo is None:
            v = v.replace(tzinfo=dt.timezone.utc)
        return v.isoformat()
    return v


def _hmac_hex(secret: str, value: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), sha256).hexdigest()


def _hmac_if_present(secret: str, v: Optional[Any]) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    return _hmac_hex(secret, s)


def redact_servicebook_entry_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redacted Export:
    - keine Klartext-PII
    - kein Freitext
    - IDs bleiben (interne IDs ok), externe/PII-Felder werden gehasht
    """
    settings = get_settings()
    secret = getattr(settings, "secret_key", None)
    if not isinstance(secret, str) or len(secret.strip()) < 16:
        # Hard fail ist ok: ohne Secret keine Pseudonymisierung.
        raise RuntimeError("missing_or_weak_secret_key")

    out: Dict[str, Any] = {}

    # stabile Meta-Felder (wenn vorhanden)
    for k in ("id", "servicebook_id", "vehicle_id", "entry_type", "category", "kind", "mileage", "odometer", "created_at"):
        if k in row and row[k] is not None:
            out[k] = _to_iso(row[k])

    # PII / sensitive -> HMAC (wenn vorhanden)
    if "vin" in row and row.get("vin"):
        out["vin_hmac"] = _hmac_hex(secret, str(row["vin"]))
        out.pop("vin", None)

    if "vehicle_id" in row and row.get("vehicle_id"):
        out["vehicle_id_hmac"] = _hmac_hex(secret, str(row["vehicle_id"]))

    if "owner_id" in row and row.get("owner_id"):
        out["owner_id_hmac"] = _hmac_hex(secret, str(row["owner_id"]))

    if "owner_email" in row and row.get("owner_email"):
        out["owner_email_hmac"] = _hmac_hex(secret, str(row["owner_email"]))

    # Freitext konsequent entfernen
    for k in list(out.keys()):
        if k.lower() in _TEXT_KEYS:
            out.pop(k, None)

    # Falls die Quelle Freitext-Felder hatte, die wir gar nicht kopiert haben: ok (sicher).
    return out
