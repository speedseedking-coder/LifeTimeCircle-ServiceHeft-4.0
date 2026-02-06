# server/app/routers/blog.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/blog", tags=["blog"])


class BlogPostSummary(BaseModel):
    slug: str = Field(..., examples=["welcome"])
    title: str = Field(..., examples=["Willkommen bei LifeTimeCircle"])
    excerpt: Optional[str] = Field(default=None, examples=["Kurzüberblick über das Service Heft 4.0…"])
    published_at: Optional[datetime] = None


class BlogPost(BlogPostSummary):
    content_md: str = Field(default="", examples=["# Willkommen\n\n…"])


# NOTE: bewusst minimal & public.
# Später: Persistenz/CRUD + RBAC für Autoren/Redaktion (nicht Teil dieses Patches).
_POSTS: dict[str, BlogPost] = {
    "welcome": BlogPost(
        slug="welcome",
        title="Willkommen bei LifeTimeCircle",
        excerpt="Warum Dokumentation Vertrauen schafft – und was das Service Heft 4.0 leistet.",
        published_at=None,
        content_md="",
    )
}


@router.get("", response_model=list[BlogPostSummary])
@router.get("/", response_model=list[BlogPostSummary])
def list_blog_posts(
    q: Optional[str] = Query(default=None, min_length=1, max_length=80),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10_000),
) -> list[BlogPostSummary]:
    items = list(_POSTS.values())
    if q:
        ql = q.lower()
        items = [p for p in items if ql in p.title.lower() or (p.excerpt and ql in p.excerpt.lower())]
    items = items[offset : offset + limit]
    return [BlogPostSummary(**p.model_dump()) for p in items]


@router.get("/{slug}", response_model=BlogPost)
def get_blog_post(slug: str) -> BlogPost:
    post = _POSTS.get(slug)
    if not post:
        raise HTTPException(status_code=404, detail="not_found")
    return post