import time
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request


@dataclass
class _Bucket:
    hits: list[float]


_STORE: dict[str, _Bucket] = {}


def rate_limit(name: str, limit: int, window_seconds: int):
    """
    In-Memory Rate-Limit (pro IP + Route-Key).
    Produktionsbetrieb: später per Redis/Shared Store ersetzen.
    """
    if limit <= 0 or window_seconds <= 0:
        raise ValueError("rate_limit: invalid parameters")

    async def _dep(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        key = f"{name}:{ip}"

        now = time.time()
        bucket = _STORE.get(key)
        if bucket is None:
            bucket = _Bucket(hits=[])
            _STORE[key] = bucket

        # prune
        cutoff = now - window_seconds
        bucket.hits = [t for t in bucket.hits if t >= cutoff]

        if len(bucket.hits) >= limit:
            raise HTTPException(status_code=429, detail="rate_limited")

        bucket.hits.append(now)

    return Depends(_dep)
