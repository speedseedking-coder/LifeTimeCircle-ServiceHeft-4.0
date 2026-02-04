from __future__ import annotations

from typing import List, Tuple, Set

from fastapi.routing import APIRoute

from app.guards import forbid_moderator
from app.main import create_app


def _routes() -> List[APIRoute]:
    app = create_app()
    return [r for r in app.routes if isinstance(r, APIRoute)]


def test_servicebook_routes_are_registered() -> None:
    paths: Set[Tuple[str, Tuple[str, ...]]] = {(r.path, tuple(sorted(r.methods or []))) for r in _routes()}

    assert ("/servicebook/{servicebook_id}/entries", ("GET",)) in paths
    assert ("/servicebook/{servicebook_id}/inspection-events", ("POST",)) in paths
    assert ("/servicebook/{servicebook_id}/cases/{case_entry_id}/remediation", ("POST",)) in paths


def test_servicebook_routes_have_forbid_moderator_dependency() -> None:
    servicebook_routes = [r for r in _routes() if r.path.startswith("/servicebook/")]
    assert servicebook_routes, "Keine /servicebook Routes gefunden (main.py include_router fehlt?)"

    for r in servicebook_routes:
        calls = [d.call for d in r.dependant.dependencies]
        assert forbid_moderator in calls, f"forbid_moderator fehlt bei Route: {r.path}"
