from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def _route_dupes(app: Any) -> list[tuple[tuple[str, tuple[str, ...], str | None], int]]:
    counts: Counter[tuple[str, tuple[str, ...], str | None]] = Counter()
    for r in getattr(app, "routes", []):
        path = getattr(r, "path", None)
        methods = tuple(sorted(getattr(r, "methods", []) or []))
        name = getattr(r, "name", None)
        if not path or not methods:
            continue
        key = (path, methods, name)
        counts[key] += 1
    return [(k, c) for k, c in counts.items() if c > 1]


def _openapi_operationid_dupes(openapi: dict[str, Any]) -> dict[str, list[tuple[str, str]]]:
    idx: dict[str, list[tuple[str, str]]] = defaultdict(list)
    paths = openapi.get("paths", {}) or {}
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if not isinstance(op, dict):
                continue
            op_id = op.get("operationId")
            if op_id:
                idx[str(op_id)].append((str(method).upper(), str(path)))
    return {op_id: locs for op_id, locs in idx.items() if len(locs) > 1}


def main() -> int:
    from app.main import app  # noqa: WPS433

    print("== Route-Dedupe (path, methods, name) ==")
    dups = _route_dupes(app)
    print("DUP_ROUTES_COUNT =", len(dups))
    for (path, methods, name), c in sorted(dups, key=lambda x: (x[0][0], x[0][1], x[0][2] or "")):
        print(f"DUP x{c}: {methods} {path} name={name!r}")

    print("\n== OpenAPI operationId Dedupe ==")
    spec = app.openapi()
    op_dups = _openapi_operationid_dupes(spec)
    print("DUP_OPERATION_ID_COUNT =", len(op_dups))
    for op_id in sorted(op_dups.keys()):
        locs = ", ".join([f"{m} {p}" for (m, p) in op_dups[op_id]])
        print(f"DUP operationId={op_id!r}: {locs}")

    if dups or op_dups:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())