# server/app/routers/news.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.cms.service import get_public_article, list_public_articles
from app.db.session import get_db

router = APIRouter(prefix="/news", tags=["news"])


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


def _as_summary(i) -> NewsItemSummary:
    return NewsItemSummary(
        slug=i.slug,
        title=i.title,
        excerpt=i.excerpt,
        published_at=i.published_at,
    )


@router.get("", response_model=list[NewsItemSummary])
@router.get("/", response_model=list[NewsItemSummary])
def list_news(db: Session = Depends(get_db)) -> list[NewsItemSummary]:
    return [_as_summary(i) for i in list_public_articles(db, "news")]


@router.get("/{slug}", response_model=NewsItem)
def get_news_item(slug: str, db: Session = Depends(get_db)) -> NewsItem:
    item = get_public_article(db, "news", slug)
    return NewsItem(
        slug=item.slug,
        title=item.title,
        excerpt=item.excerpt,
        published_at=item.published_at,
        content_md=item.content_md,
    )
