from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid4_str() -> str:
    return str(uuid.uuid4())


class CmsArticle(Base):
    __tablename__ = "cms_articles"

    article_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid4_str)
    content_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt: Mapped[str] = mapped_column(String(500), nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    workflow_state: Mapped[str] = mapped_column(String(16), nullable=False, index=True, default="draft")

    author_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewer_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    published_by_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("content_type", "slug", name="uq_cms_article_type_slug"),
        Index("ix_cms_article_type_state", "content_type", "workflow_state"),
    )
