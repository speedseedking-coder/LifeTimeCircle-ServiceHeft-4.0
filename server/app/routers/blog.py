# server/app/routers/blog.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/blog", tags=["blog"])

_CET = timezone(timedelta(hours=1))


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


_POSTS: dict[str, BlogPost] = {
    "welcome": BlogPost(
        slug="welcome",
        title="Willkommen bei LifeTimeCircle",
        excerpt="Warum Dokumentation Vertrauen schafft – und was das Service Heft 4.0 leistet.",
        published_at=datetime(2026, 2, 6, 10, 0, 0, tzinfo=_CET),
        content_md=(
            "# Willkommen bei LifeTimeCircle\n\n"
            "Aus einem Gebrauchtwagen wird ein **dokumentiertes Vertrauensgut**, wenn Nachweise sauber, prüfbar und "
            "durchgängig sind.\n\n"
            "## Was das Service Heft 4.0 macht\n\n"
            "- sammelt Wartung/Inspektion/Reparaturen strukturiert\n"
            "- verknüpft Ereignisse mit **Dokumenten** (Rechnungen, Prüfberichte, Fotos)\n"
            "- setzt Security-by-Default: **Uploads gehen in Quarantäne**, Freigabe erst nach Scan + Admin-Approve\n"
            "- schützt vor Datenabfluss: RBAC serverseitig, least privilege\n\n"
            "## Trust-Ampel\n\n"
            "„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. "
            "Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“\n"
        ),
    )
}


def _as_summary(p: BlogPost) -> BlogPostSummary:
    return BlogPostSummary(
        slug=p.slug,
        title=p.title,
        excerpt=p.excerpt,
        published_at=p.published_at,
    )


@router.get("", response_model=list[BlogPostSummary])
@router.get("/", response_model=list[BlogPostSummary])
def list_blog_posts() -> list[BlogPostSummary]:
    posts = sorted(
        _POSTS.values(),
        key=lambda p: p.published_at or datetime(1970, 1, 1, tzinfo=timezone.utc),
        reverse=True,
    )
    return [_as_summary(p) for p in posts]


@router.get("/{slug}", response_model=BlogPost)
def get_blog_post(slug: str) -> BlogPost:
    post = _POSTS.get(slug)
    if not post:
        raise HTTPException(status_code=404, detail="not_found")
    return post