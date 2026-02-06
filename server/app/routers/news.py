# server/app/routers/news.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/news", tags=["news"])


class NewsItemSummary(BaseModel):
    slug: str = Field(..., examples=["release-notes-2026-02"])
    title: str = Field(..., examples=["Release Notes – Februar 2026"])
    excerpt: Optional[str] = Field(default=None, examples=["Neu: Upload-Quarantäne…"])
    published_at: Optional[datetime] = None


class NewsItem(NewsItemSummary):
    content_md: str = Field(default="", examples=["# Release Notes\n\n…"])


# NOTE: bewusst minimal & public.
_ITEMS: dict[str, NewsItem] = {
    "release-notes-2026-02": NewsItem(
        slug="release-notes-2026-02",
        title="Release Notes – Februar 2026",
        excerpt="Security: Uploads in Quarantäne-by-default, Admin Scan/Approve.",
        published_at=None,
        content_md="",
    )
}


@router.get("", response_model=list[NewsItemSummary])
@router.get("/", response_model=list[NewsItemSummary])
def list_news(
    q: Optional[str] = Query(default=None, min_length=1, max_length=80),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10_000),
) -> list[NewsItemSummary]:
    items = list(_ITEMS.values())
    if q:
        ql = q.lower()
        items = [n for n in items if ql in n.title.lower() or (n.excerpt and ql in n.excerpt.lower())]
    items = items[offset : offset + limit]
    return [NewsItemSummary(**n.model_dump()) for n in items]


@router.get("/{slug}", response_model=NewsItem)
def get_news_item(slug: str) -> NewsItem:
    item = _ITEMS.get(slug)
    if not item:
        raise HTTPException(status_code=404, detail="not_found")
    return item