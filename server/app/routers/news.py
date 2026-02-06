# server/app/routers/news.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/news", tags=["news"])

_CET = timezone(timedelta(hours=1))


class NewsItemSummary(BaseModel):
    slug: str = Field(..., examples=["release-notes-2026-02"])
    title: str = Field(..., examples=["Release Notes – Februar 2026"])
    excerpt: str = Field(
        ...,
        examples=["Security: Uploads in Quarantäne-by-default, Admin Scan/Approve."],
    )
    published_at: Optional[datetime] = None


class NewsItem(NewsItemSummary):
    content_md: str = Field(default="", examples=["# Release Notes\n\n…"])


_ITEMS: dict[str, NewsItem] = {
    "release-notes-2026-02": NewsItem(
        slug="release-notes-2026-02",
        title="Release Notes – Februar 2026",
        excerpt="Security: Uploads in Quarantäne-by-default, Admin Scan/Approve.",
        published_at=datetime(2026, 2, 6, 10, 0, 0, tzinfo=_CET),
        content_md=(
            "# Release Notes – Februar 2026\n\n"
            "## Security / RBAC\n\n"
            "- **Uploads in Quarantäne-by-default**: neue Dokumente werden nicht ausgeliefert, bevor sie gescannt und "
            "durch Admin freigegeben sind.\n"
            "- **Approve nur bei Scan=CLEAN** (sonst 409).\n"
            "- **Moderator** bleibt strikt auf **Blog/News** limitiert.\n\n"
            "## Sale/Transfer\n\n"
            "- `GET /sale/transfer/status/{transfer_id}` ist zusätzlich **object-level** geschützt: nur **Initiator** "
            "oder **Redeemer** (sonst 403), um ID-Leaks via Transfer-ID zu verhindern.\n\n"
            "## Public Content\n\n"
            "- Public Endpoints für **Blog/News**: `GET /blog(/)`, `GET /blog/{slug}`, `GET /news(/)`, `GET /news/{slug}`.\n\n"
            "## Hinweis\n\n"
            "- Beim Start können FastAPI-Warnings zu **Duplicate Operation ID** aus `app/routers/documents.py` erscheinen. "
            "Tests sind grün; Cleanup später (operation_id explizit setzen / Doppel-Decorator prüfen).\n"
        ),
    )
}


def _as_summary(i: NewsItem) -> NewsItemSummary:
    return NewsItemSummary(
        slug=i.slug,
        title=i.title,
        excerpt=i.excerpt,
        published_at=i.published_at,
    )


@router.get("", response_model=list[NewsItemSummary])
@router.get("/", response_model=list[NewsItemSummary])
def list_news() -> list[NewsItemSummary]:
    items = sorted(
        _ITEMS.values(),
        key=lambda i: i.published_at or datetime(1970, 1, 1, tzinfo=timezone.utc),
        reverse=True,
    )
    return [_as_summary(i) for i in items]


@router.get("/{slug}", response_model=NewsItem)
def get_news_item(slug: str) -> NewsItem:
    item = _ITEMS.get(slug)
    if not item:
        raise HTTPException(status_code=404, detail="not_found")
    return item