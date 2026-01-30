from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .storage import rate_limit_get, rate_limit_set


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def check_and_inc(conn, key: str, window_seconds: int, limit: int) -> bool:
    """
    True = erlaubt, False = blockiert
    Simple fixed window counter in SQLite.
    """
    now = _utc_now()
    row = rate_limit_get(conn, key)
    if row is None:
        rate_limit_set(conn, key, _iso(now), 1)
        return True

    window_start = datetime.fromisoformat(row["window_start"])
    count = int(row["count"])

    if now - window_start >= timedelta(seconds=window_seconds):
        rate_limit_set(conn, key, _iso(now), 1)
        return True

    if count >= limit:
        return False

    rate_limit_set(conn, key, _iso(window_start), count + 1)
    return True
