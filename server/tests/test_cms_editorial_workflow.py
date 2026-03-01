from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.rbac import AuthContext, get_current_user
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


def _setup() -> tuple[TestClient, dict[str, AuthContext]]:
    app = create_app()
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

    actor_holder = {"actor": AuthContext(user_id="mod-1", role="moderator")}

    def _get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = lambda: actor_holder["actor"]

    return TestClient(app), actor_holder


def test_public_blog_and_news_use_seeded_articles() -> None:
    client, _actor_holder = _setup()

    blog_res = client.get("/blog")
    assert blog_res.status_code == 200, blog_res.text
    blog_items = blog_res.json()
    assert [row["slug"] for row in blog_items[:3]] == [
        "spring-maintenance-2026",
        "trust-ampel-guide",
        "digital-vehicle-passport",
    ]

    news_res = client.get("/news")
    assert news_res.status_code == 200, news_res.text
    news_items = news_res.json()
    assert [row["slug"] for row in news_items[:3]] == [
        "eu-digital-vehicle-passport-2027",
        "ltc-expands-to-fleet-management",
        "trust-ampel-reaches-100k-vehicles",
    ]


def test_editorial_flow_requires_review_and_superadmin_publish() -> None:
    client, actor_holder = _setup()

    create_res = client.post(
        "/cms/blog/drafts",
        json={
            "slug": "moderator-draft",
            "title": "Moderator Draft",
            "excerpt": "Kurzer Entwurf fuer den Review-Flow im CMS.",
            "content_md": "Erster Entwurf fuer den Review-Flow.\n\n- Abschnitt eins\n- Abschnitt zwei",
        },
    )
    assert create_res.status_code == 200, create_res.text
    article = create_res.json()
    article_id = article["article_id"]
    assert article["workflow_state"] == "draft"

    submit_res = client.post(f"/cms/blog/{article_id}/submit")
    assert submit_res.status_code == 200, submit_res.text
    assert submit_res.json()["workflow_state"] == "in_review"

    publish_as_mod = client.post(f"/cms/publish/{article_id}")
    assert publish_as_mod.status_code == 403, publish_as_mod.text

    actor_holder["actor"] = AuthContext(user_id="admin-1", role="admin")
    publish_as_admin = client.post(f"/cms/publish/{article_id}")
    assert publish_as_admin.status_code == 403, publish_as_admin.text

    review_res = client.post(
        f"/cms/review/blog/{article_id}",
        json={"review_note": "Fachlich ok, finaler Publish bleibt bei Superadmin."},
    )
    assert review_res.status_code == 200, review_res.text
    reviewed_article = review_res.json()
    assert reviewed_article["workflow_state"] == "in_review"
    assert reviewed_article["review_note"] == "Fachlich ok, finaler Publish bleibt bei Superadmin."
    assert reviewed_article["reviewed_at"]

    actor_holder["actor"] = AuthContext(user_id="super-1", role="superadmin")
    publish_res = client.post(f"/cms/publish/{article_id}")
    assert publish_res.status_code == 200, publish_res.text
    published = publish_res.json()
    assert published["workflow_state"] == "published"
    assert published["published_at"]

    public_res = client.get("/blog/moderator-draft")
    assert public_res.status_code == 200, public_res.text
    assert public_res.json()["title"] == "Moderator Draft"
