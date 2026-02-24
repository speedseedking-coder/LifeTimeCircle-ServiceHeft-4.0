from __future__ import annotations

import re
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

_HDR = "x-request-id"
_VALID = re.compile(r"^[A-Za-z0-9._:-]{6,128}$")

class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    - accepts X-Request-Id if valid-ish
    - else generates UUID4
    - stores request_id on request.state.request_id
    - writes X-Request-Id to every response
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get(_HDR)
        if not rid or not _VALID.match(rid):
            rid = str(uuid.uuid4())

        request.state.request_id = rid

        response = await call_next(request)
        response.headers["X-Request-Id"] = rid
        return response
