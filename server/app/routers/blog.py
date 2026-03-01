# server/app/routers/blog.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.cms.service import get_public_article, list_public_articles
from app.db.session import get_db

router = APIRouter(prefix="/blog", tags=["blog"])


class BlogPostSummary(BaseModel):
    slug: str = Field(..., examples=["welcome"])
    title: str = Field(..., examples=["Willkommen bei LifeTimeCircle"])
    excerpt: str = Field(
        ...,
        examples=[
            "Warum Dokumentation Vertrauen schafft – und was das Service Heft 4.0 leistet."
        ],
    )
    published_at: Optional[datetime] = None


class BlogPost(BlogPostSummary):
    content_md: str = Field(default="", examples=["# Willkommen\n\n…"])


def _as_summary(p) -> BlogPostSummary:
    return BlogPostSummary(
        slug=p.slug,
        title=p.title,
        excerpt=p.excerpt,
        published_at=p.published_at,
    )


@router.get("", response_model=list[BlogPostSummary])
@router.get("/", response_model=list[BlogPostSummary])
def list_blog_posts(db: Session = Depends(get_db)) -> list[BlogPostSummary]:
    return [_as_summary(p) for p in list_public_articles(db, "blog")]


@router.get("/{slug}", response_model=BlogPost)
def get_blog_post(slug: str, db: Session = Depends(get_db)) -> BlogPost:
    post = get_public_article(db, "blog", slug)
    return BlogPost(
        slug=post.slug,
        title=post.title,
        excerpt=post.excerpt,
        published_at=post.published_at,
        content_md=post.content_md,
    )
