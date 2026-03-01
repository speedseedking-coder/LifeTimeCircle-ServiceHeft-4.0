from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.deps import require_admin, require_moderator, require_superadmin
from app.auth.rbac import AuthContext
from app.cms.service import (
    CmsContentType,
    create_draft,
    get_editorial_article,
    list_editorial_articles,
    mark_reviewed,
    publish_article,
    submit_for_review,
    update_article,
    validate_slug,
)
from app.db.session import get_db
from app.guards import forbid_moderator


router = APIRouter(prefix="/cms", tags=["cms"])

WorkflowState = Literal["draft", "in_review", "published"]


class CmsArticleSummary(BaseModel):
    article_id: str
    content_type: Literal["blog", "news"]
    slug: str
    title: str
    excerpt: str
    workflow_state: WorkflowState
    review_note: str | None = None
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    published_at: datetime | None = None


class CmsArticleDetail(CmsArticleSummary):
    content_md: str


class CmsDraftPayload(BaseModel):
    slug: str = Field(..., min_length=3, max_length=160)
    title: str = Field(..., min_length=3, max_length=255)
    excerpt: str = Field(..., min_length=8, max_length=500)
    content_md: str = Field(..., min_length=16, max_length=12000)


class CmsReviewPayload(BaseModel):
    review_note: str | None = Field(default=None, max_length=1200)


def _to_summary(article) -> CmsArticleSummary:
    return CmsArticleSummary(
        article_id=article.article_id,
        content_type=article.content_type,
        slug=article.slug,
        title=article.title,
        excerpt=article.excerpt,
        workflow_state=article.workflow_state,
        review_note=article.review_note,
        created_at=article.created_at,
        updated_at=article.updated_at,
        submitted_at=article.submitted_at,
        reviewed_at=article.reviewed_at,
        published_at=article.published_at,
    )


def _to_detail(article) -> CmsArticleDetail:
    return CmsArticleDetail(**_to_summary(article).model_dump(), content_md=article.content_md)


def _list_articles(content_type: CmsContentType, db: Session) -> list[CmsArticleSummary]:
    rows = list_editorial_articles(db, content_type)
    return [_to_summary(row) for row in rows]


def _get_article(content_type: CmsContentType, article_id: str, db: Session) -> CmsArticleDetail:
    article = get_editorial_article(db, content_type=content_type, article_id=article_id)
    return _to_detail(article)


def _create_article(
    content_type: CmsContentType,
    payload: CmsDraftPayload,
    db: Session,
    actor: AuthContext,
) -> CmsArticleDetail:
    article = create_draft(
        db,
        content_type=content_type,
        actor=actor,
        slug=validate_slug(payload.slug),
        title=payload.title.strip(),
        excerpt=payload.excerpt.strip(),
        content_md=payload.content_md.strip(),
    )
    return _to_detail(article)


def _update_article(
    content_type: CmsContentType,
    article_id: str,
    payload: CmsDraftPayload,
    db: Session,
    actor: AuthContext,
) -> CmsArticleDetail:
    article = update_article(
        db,
        content_type=content_type,
        article_id=article_id,
        actor=actor,
        slug=validate_slug(payload.slug),
        title=payload.title.strip(),
        excerpt=payload.excerpt.strip(),
        content_md=payload.content_md.strip(),
    )
    return _to_detail(article)


def _submit_article(content_type: CmsContentType, article_id: str, db: Session) -> CmsArticleDetail:
    article = submit_for_review(db, content_type=content_type, article_id=article_id)
    return _to_detail(article)


def _review_article(
    content_type: CmsContentType,
    article_id: str,
    payload: CmsReviewPayload,
    db: Session,
    actor: AuthContext,
) -> CmsArticleDetail:
    article = mark_reviewed(
        db,
        content_type=content_type,
        article_id=article_id,
        actor=actor,
        review_note=payload.review_note,
    )
    return _to_detail(article)


@router.get("/blog", response_model=list[CmsArticleSummary])
def cms_list_blog_articles(
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_moderator),
) -> list[CmsArticleSummary]:
    return _list_articles("blog", db)


@router.get("/blog/{article_id}", response_model=CmsArticleDetail)
def cms_get_blog_article(
    article_id: str,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_moderator),
) -> CmsArticleDetail:
    return _get_article("blog", article_id, db)


@router.post("/blog/drafts", response_model=CmsArticleDetail)
def cms_create_blog_draft(
    payload: CmsDraftPayload,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_moderator),
) -> CmsArticleDetail:
    return _create_article("blog", payload, db, actor)


@router.post("/blog/{article_id}", response_model=CmsArticleDetail)
def cms_update_blog_article(
    article_id: str,
    payload: CmsDraftPayload,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_moderator),
) -> CmsArticleDetail:
    return _update_article("blog", article_id, payload, db, actor)


@router.post("/blog/{article_id}/submit", response_model=CmsArticleDetail)
def cms_submit_blog_for_review(
    article_id: str,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_moderator),
) -> CmsArticleDetail:
    return _submit_article("blog", article_id, db)


@router.post(
    "/review/blog/{article_id}",
    response_model=CmsArticleDetail,
    dependencies=[Depends(forbid_moderator)],
)
def cms_review_blog_article(
    article_id: str,
    payload: CmsReviewPayload,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_admin),
) -> CmsArticleDetail:
    return _review_article("blog", article_id, payload, db, actor)


@router.get("/news", response_model=list[CmsArticleSummary])
def cms_list_news_articles(
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_moderator),
) -> list[CmsArticleSummary]:
    return _list_articles("news", db)


@router.get("/news/{article_id}", response_model=CmsArticleDetail)
def cms_get_news_article(
    article_id: str,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_moderator),
) -> CmsArticleDetail:
    return _get_article("news", article_id, db)


@router.post("/news/drafts", response_model=CmsArticleDetail)
def cms_create_news_draft(
    payload: CmsDraftPayload,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_moderator),
) -> CmsArticleDetail:
    return _create_article("news", payload, db, actor)


@router.post("/news/{article_id}", response_model=CmsArticleDetail)
def cms_update_news_article(
    article_id: str,
    payload: CmsDraftPayload,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_moderator),
) -> CmsArticleDetail:
    return _update_article("news", article_id, payload, db, actor)


@router.post("/news/{article_id}/submit", response_model=CmsArticleDetail)
def cms_submit_news_for_review(
    article_id: str,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_moderator),
) -> CmsArticleDetail:
    return _submit_article("news", article_id, db)


@router.post(
    "/review/news/{article_id}",
    response_model=CmsArticleDetail,
    dependencies=[Depends(forbid_moderator)],
)
def cms_review_news_article(
    article_id: str,
    payload: CmsReviewPayload,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_admin),
) -> CmsArticleDetail:
    return _review_article("news", article_id, payload, db, actor)


@router.post(
    "/publish/{article_id}",
    response_model=CmsArticleDetail,
    dependencies=[Depends(forbid_moderator)],
)
def cms_publish_article(
    article_id: str,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_superadmin),
) -> CmsArticleDetail:
    article = publish_article(db, article_id=article_id, actor=actor)
    return _to_detail(article)
