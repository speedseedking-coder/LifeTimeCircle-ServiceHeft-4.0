from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.rbac import AuthContext
from app.models.cms import CmsArticle

CmsContentType = Literal["blog", "news"]
CmsWorkflowState = Literal["draft", "in_review", "published"]

CMS_EDITOR_ROLES = ("moderator", "admin", "superadmin")
CMS_REVIEWER_ROLES = ("admin", "superadmin")
CMS_PUBLISHER_ROLES = ("superadmin",)


@dataclass(frozen=True)
class SeedArticle:
    slug: str
    title: str
    excerpt: str
    content_md: str
    published_at: datetime


_SEED: dict[CmsContentType, tuple[SeedArticle, ...]] = {
    "blog": (
        SeedArticle(
            slug="spring-maintenance-2026",
            title="Nachweise statt Behauptung: So wird Fahrzeughistorie belastbar",
            excerpt=(
                "Eine belastbare Fahrzeughistorie entsteht nicht durch Stichworte, "
                "sondern durch nachvollziehbare Eintraege, Belege und klare Zuordnung."
            ),
            content_md=(
                "Eine belastbare Fahrzeughistorie beginnt nicht mit einer grossen Behauptung, "
                "sondern mit einem sauberen Eintrag und einem passenden Nachweis.\n\n"
                "**Was in jeden guten Eintrag gehoert:**\n"
                "- Datum der Arbeit\n"
                "- Typ des Eintrags\n"
                "- durchgefuehrt von\n"
                "- Kilometerstand\n"
                "- kurze, sachliche Beschreibung\n\n"
                "**Welche Nachweise den Unterschied machen:**\n"
                "- Rechnung oder Werkstattbeleg\n"
                "- Pruefbericht oder Gutachten\n"
                "- Foto der Arbeit oder des Bauteils\n"
                "- Zusatzdokumente nur dann, wenn sie zum Eintrag passen\n\n"
                "Wenn Eintraege und Nachweise sauber zusammengehoeren, wird Historie nachvollziehbar. "
                "Genau darauf baut das Service Heft 4.0 auf."
            ),
            published_at=datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc),
        ),
        SeedArticle(
            slug="trust-ampel-guide",
            title="Trust-Ampel richtig lesen: Dokumentationsqualitaet statt Technikurteil",
            excerpt=(
                "Die Trust-Ampel beschreibt, wie gut Historie und Nachweise dokumentiert sind. "
                "Sie ist bewusst keine technische Diagnose."
            ),
            content_md=(
                "Die Trust-Ampel zeigt, wie gut eine Fahrzeughistorie dokumentiert und nachweisbar ist. "
                "Sie bewertet nicht, ob ein Fahrzeug technisch gut oder schlecht ist.\n\n"
                "**So lesen Sie die Anzeige richtig:**\n"
                "- GRUEN steht fuer gut belegte und nachvollziehbare Historie\n"
                "- GELB zeigt, dass Dokumentation vorhanden ist, aber Luecken bleiben\n"
                "- ORANGE oder ROT weisen auf geringe Nachweisqualitaet oder fehlende Belege hin\n\n"
                "**Was die Bewertung verbessert:**\n"
                "- Eintraege vollstaendig anlegen\n"
                "- Nachweise direkt am passenden Eintrag hochladen\n"
                "- Unfall- und Pruefkontexte nicht weglassen\n"
                "- Dokumentation aktuell und plausibel halten\n\n"
                "Die Trust-Ampel bleibt damit ein Werkzeug fuer Dokumentationsqualitaet. "
                "Sie ersetzt keine technische Pruefung und kein Gutachten."
            ),
            published_at=datetime(2026, 2, 28, 9, 0, tzinfo=timezone.utc),
        ),
        SeedArticle(
            slug="digital-vehicle-passport",
            title="Serviceeintraege sauber vorbereiten: Welche Angaben wirklich helfen",
            excerpt=(
                "Datum, Typ, durchgefuehrt von, Kilometerstand und passender Nachweis machen "
                "aus einem Eintrag eine pruefbare Historie."
            ),
            content_md=(
                "Ein Eintrag wird erst dann nuetzlich, wenn er fuer andere lesbar und pruefbar bleibt. "
                "Dafuer helfen wenige Pflichtangaben mehr als viel Freitext.\n\n"
                "**Diese Felder sollten sauber gepflegt sein:**\n"
                "- Datum\n"
                "- Typ\n"
                "- durchgefuehrt von\n"
                "- Kilometerstand\n"
                "- kurze Bemerkung nur mit relevanten Fakten\n\n"
                "**Typische Fehler, die Trust kosten:**\n"
                "- unklare Werkstatt- oder Quellenangaben\n"
                "- fehlender Kilometerstand\n"
                "- Beleg ohne Bezug zum Eintrag\n"
                "- Fotos oder PDFs ohne erkennbaren Kontext\n\n"
                "Wenn du diese Punkte konsequent pflegst, steigen Nachvollziehbarkeit, Trust-Stufe "
                "und Qualitaet des gesamten Verlaufs."
            ),
            published_at=datetime(2026, 2, 25, 9, 0, tzinfo=timezone.utc),
        ),
    ),
    "news": (
        SeedArticle(
            slug="eu-digital-vehicle-passport-2027",
            title="Produktstatus: Public-QR bleibt bewusst datenarm",
            excerpt=(
                "Der oeffentliche Mini-Check zeigt nur Ampel und textliche Indikatoren. "
                "Kennzahlen, Downloads und Technikdiagnosen bleiben bewusst aussen vor."
            ),
            content_md=(
                "Der Public-QR Mini-Check bleibt bewusst knapp. Er zeigt nur das, was oeffentlich "
                "vertretbar und fachlich sinnvoll ist.\n\n"
                "**Was sichtbar ist:**\n"
                "- Ampel Rot, Orange, Gelb oder Gruen\n"
                "- kurze textliche Hinweise zur Dokumentationsqualitaet\n"
                "- keine Halterdaten und keine Technikdiagnose\n\n"
                "**Was bewusst nicht sichtbar ist:**\n"
                "- keine Kennzahlen oder Prozentwerte\n"
                "- keine Dokumente oder Downloads\n"
                "- keine internen Freigaben, keine PII und keine Diagnosedaten\n\n"
                "Damit bleibt der oeffentliche Einstieg nuetzlich, ohne in Detaildaten oder "
                "sicherheitskritische Bereiche zu kippen."
            ),
            published_at=datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc),
        ),
        SeedArticle(
            slug="ltc-expands-to-fleet-management",
            title="Produktupdate: Uploads starten weiterhin in Quarantaene",
            excerpt=(
                "Nachweise werden zuerst geprueft. Erst danach sind sie im vorgesehenen Flow "
                "nutzbar. Das schuetzt Public- und Kernbereiche vor ungeprueften Dateien."
            ),
            content_md=(
                "Dokumente und Nachweise werden im Produktfluss nicht ungeprueft durchgereicht. "
                "Uploads starten weiterhin im Pruefpfad.\n\n"
                "**Warum dieser Schritt wichtig ist:**\n"
                "- ungepruefte Dateien landen nicht direkt im vorgesehenen Nutzpfad\n"
                "- Freigaben bleiben an Scan- und Admin-Status gekoppelt\n"
                "- Public- und Kernansichten zeigen keine Dokumente ohne vorgesehenen Status\n\n"
                "**Was das fuer Nutzer bedeutet:**\n"
                "- Upload zuerst sauber zuordnen\n"
                "- Status pruefen\n"
                "- bei Bedarf im Admin- oder Dokumenten-Flow nacharbeiten\n\n"
                "Das ist kein Komfortdetail, sondern Teil der Sicherheits- und Governance-Logik des Produkts."
            ),
            published_at=datetime(2026, 2, 27, 9, 0, tzinfo=timezone.utc),
        ),
        SeedArticle(
            slug="trust-ampel-reaches-100k-vehicles",
            title="Governance: Moderator bleibt strikt auf Blog und News begrenzt",
            excerpt=(
                "Die Rollenlogik bleibt eng: Moderator bearbeitet Inhalte, aber keine Fahrzeug-, "
                "Dokument- oder Admin-Prozesse."
            ),
            content_md=(
                "Die Rollenlogik bleibt eng und absichtlich unspektakulaer. Moderator ist fuer "
                "Inhaltsflaechen da, nicht fuer operative Fahrzeug- oder Governance-Aktionen.\n\n"
                "**Das bedeutet konkret:**\n"
                "- Blog und News bleiben der vorgesehene Bereich fuer Moderation\n"
                "- Fahrzeuge, Dokumente, Export und Admin bleiben serverseitig geschuetzt\n"
                "- hohe Rechte und sensible Freigaben bleiben bei Admin oder Superadmin\n\n"
                "**Warum das wichtig ist:**\n"
                "- geringere Angriffsflaeche\n"
                "- klare Verantwortlichkeiten\n"
                "- weniger Risiko fuer Fehlbedienung in sensiblen Bereichen\n\n"
                "Die Rollenwahrheit ist damit kein Nebensatz in der Doku, sondern fester Teil des Produktverhaltens."
            ),
            published_at=datetime(2026, 2, 20, 9, 0, tzinfo=timezone.utc),
        ),
    ),
}


def ensure_seed_articles(db: Session) -> None:
    seeded = False
    for content_type, articles in _SEED.items():
        existing = {
            slug
            for slug in db.scalars(select(CmsArticle.slug).where(CmsArticle.content_type == content_type)).all()
        }
        for article in articles:
            if article.slug in existing:
                continue
            db.add(
                CmsArticle(
                    content_type=content_type,
                    slug=article.slug,
                    title=article.title,
                    excerpt=article.excerpt,
                    content_md=article.content_md,
                    workflow_state="published",
                    author_user_id="system",
                    reviewer_user_id="system",
                    published_by_user_id="system",
                    submitted_at=article.published_at,
                    reviewed_at=article.published_at,
                    published_at=article.published_at,
                )
            )
            seeded = True
    if seeded:
        db.commit()


def validate_content_type(raw_value: str) -> CmsContentType:
    value = (raw_value or "").strip().lower()
    if value in {"blog", "news"}:
        return value
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")


def validate_slug(raw_value: str) -> str:
    value = (raw_value or "").strip().lower()
    if len(value) < 3 or len(value) > 160:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_slug")
    for ch in value:
        if ch.islower() or ch.isdigit() or ch == "-":
            continue
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_slug")
    return value


def get_editorial_article(db: Session, *, content_type: CmsContentType, article_id: str) -> CmsArticle:
    ensure_seed_articles(db)
    article = db.scalar(
        select(CmsArticle)
        .where(CmsArticle.content_type == content_type, CmsArticle.article_id == article_id)
        .limit(1)
    )
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return article


def list_public_articles(db: Session, content_type: CmsContentType) -> list[CmsArticle]:
    ensure_seed_articles(db)
    rows = db.scalars(
        select(CmsArticle)
        .where(CmsArticle.content_type == content_type, CmsArticle.workflow_state == "published")
        .order_by(CmsArticle.published_at.desc(), CmsArticle.updated_at.desc())
    ).all()
    return list(rows)


def get_public_article(db: Session, content_type: CmsContentType, slug: str) -> CmsArticle:
    ensure_seed_articles(db)
    article = db.scalar(
        select(CmsArticle)
        .where(CmsArticle.content_type == content_type, CmsArticle.slug == slug, CmsArticle.workflow_state == "published")
        .limit(1)
    )
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return article


def list_editorial_articles(db: Session, content_type: CmsContentType) -> list[CmsArticle]:
    ensure_seed_articles(db)
    rows = db.scalars(
        select(CmsArticle)
        .where(CmsArticle.content_type == content_type)
        .order_by(
            CmsArticle.published_at.desc().nullslast(),
            CmsArticle.updated_at.desc(),
            CmsArticle.created_at.desc(),
        )
    ).all()
    return list(rows)


def create_draft(
    db: Session,
    *,
    content_type: CmsContentType,
    actor: AuthContext,
    slug: str,
    title: str,
    excerpt: str,
    content_md: str,
) -> CmsArticle:
    ensure_seed_articles(db)
    _ensure_unique_slug(db, content_type=content_type, slug=slug, ignore_article_id=None)
    article = CmsArticle(
        content_type=content_type,
        slug=slug,
        title=title,
        excerpt=excerpt,
        content_md=content_md,
        workflow_state="draft",
        author_user_id=actor.user_id,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def update_article(
    db: Session,
    *,
    content_type: CmsContentType,
    article_id: str,
    actor: AuthContext,
    slug: str,
    title: str,
    excerpt: str,
    content_md: str,
) -> CmsArticle:
    article = get_editorial_article(db, content_type=content_type, article_id=article_id)
    if article.workflow_state == "published" and actor.role != "superadmin":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="published_article_read_only")

    _ensure_unique_slug(db, content_type=content_type, slug=slug, ignore_article_id=article.article_id)

    article.slug = slug
    article.title = title
    article.excerpt = excerpt
    article.content_md = content_md

    if actor.role != "superadmin" and article.workflow_state != "draft":
        article.workflow_state = "draft"
        article.reviewer_user_id = None
        article.review_note = None
        article.reviewed_at = None
        article.published_by_user_id = None
        article.published_at = None
        article.submitted_at = None

    db.commit()
    db.refresh(article)
    return article


def submit_for_review(
    db: Session,
    *,
    content_type: CmsContentType,
    article_id: str,
) -> CmsArticle:
    article = get_editorial_article(db, content_type=content_type, article_id=article_id)
    if article.workflow_state == "published":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="published_article_read_only")
    article.workflow_state = "in_review"
    article.submitted_at = datetime.now(timezone.utc)
    article.review_note = None
    article.reviewer_user_id = None
    article.reviewed_at = None
    db.commit()
    db.refresh(article)
    return article


def mark_reviewed(
    db: Session,
    *,
    content_type: CmsContentType,
    article_id: str,
    actor: AuthContext,
    review_note: str | None,
) -> CmsArticle:
    article = get_editorial_article(db, content_type=content_type, article_id=article_id)
    if article.workflow_state == "published":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="published_article_read_only")
    article.workflow_state = "in_review"
    article.reviewer_user_id = actor.user_id
    article.review_note = (review_note or "").strip() or None
    article.reviewed_at = datetime.now(timezone.utc)
    if article.submitted_at is None:
        article.submitted_at = article.reviewed_at
    db.commit()
    db.refresh(article)
    return article


def publish_article(db: Session, *, article_id: str, actor: AuthContext) -> CmsArticle:
    ensure_seed_articles(db)
    article = db.scalar(select(CmsArticle).where(CmsArticle.article_id == article_id).limit(1))
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if article.workflow_state != "in_review" or article.reviewed_at is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="review_required")

    article.workflow_state = "published"
    article.published_by_user_id = actor.user_id
    article.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(article)
    return article


def _ensure_unique_slug(
    db: Session,
    *,
    content_type: CmsContentType,
    slug: str,
    ignore_article_id: str | None,
) -> None:
    existing = db.scalar(
        select(CmsArticle)
        .where(CmsArticle.content_type == content_type, CmsArticle.slug == slug)
        .limit(1)
    )
    if existing is not None and existing.article_id != ignore_article_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="slug_conflict")
