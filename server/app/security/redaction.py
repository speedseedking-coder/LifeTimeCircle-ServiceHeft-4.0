from __future__ import annotations

FORBIDDEN_KEYS = {
    "email", "e-mail", "mail",
    "phone", "telefon",
    "token", "access_token", "refresh_token",
    "authorization", "cookie", "set-cookie",
    "password", "passwort",
    "vin",
}

def redact_metadata(metadata: dict | None, allowlist: set[str] | None = None) -> dict:
    """
    deny-by-default:
      - if allowlist provided: keep only allowlisted keys
      - always drop forbidden keys (case-insensitive)
      - never include nested structures unless explicitly allowlisted (kept as-is)
    """
    if not metadata:
        return {}

    allow = set(allowlist or [])
    out: dict = {}

    for k, v in metadata.items():
        key = str(k)
        kl = key.lower()

        if kl in FORBIDDEN_KEYS:
            continue

        if allow:
            if key in allow:
                out[key] = v
            continue

        # deny-by-default if no allowlist: keep nothing
        continue

    return out
