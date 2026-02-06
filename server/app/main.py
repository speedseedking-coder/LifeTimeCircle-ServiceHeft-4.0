from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from app.auth.routes import router as auth_router
from app.admin.routes import router as admin_router
from app.core.config import get_settings
from app.db.session import init_db
from app.guards import forbid_moderator
from app.public.routes import router as public_router
from app.routers.consent import router as consent_router
from app.routers.documents import router as documents_router
from app.routers.export import router as export_router
from app.routers.export_servicebook import router as export_servicebook_router
from app.routers.export_vehicle import router as export_vehicle_router
from app.routers.masterclipboard import router as masterclipboard_router
from app.routers.sale_transfer import router as sale_transfer_router

# Package-Module Router (ohne documents!)
from app.routers import servicebook, blog, news


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # DB initialisieren (create_all – migrations folgen später)
        init_db()
        yield

    app = FastAPI(
        title="LifeTimeCircle – ServiceHeft 4.0",
        version="0.1.0",
        docs_url="/docs" if settings.env != "prod" else None,
        redoc_url="/redoc" if settings.env != "prod" else None,
        openapi_url="/openapi.json" if settings.env != "prod" else None,
        lifespan=lifespan,
    )

    # Router
    app.include_router(auth_router)
    app.include_router(masterclipboard_router)
    app.include_router(export_router)

    app.include_router(admin_router)
    app.include_router(public_router)

    app.include_router(export_vehicle_router)
    app.include_router(export_servicebook_router)

    app.include_router(consent_router)
    app.include_router(sale_transfer_router)

    # ✅ Documents NUR EINMAL
    app.include_router(documents_router)

    app.include_router(servicebook.router)

    # Blog/News (public)
    app.include_router(blog.router)
    app.include_router(news.router)

    @app.get("/health", include_in_schema=False, dependencies=[Depends(forbid_moderator)])
    def health() -> dict:
        return {"ok": True}

    # Minimaler Exception-Fallback (keine Payload-Logs)
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_, exc: Exception):
        # Keine Details rausgeben (prod-sicher). In dev nur generisch.
        if settings.env == "dev":
            return JSONResponse(status_code=500, content={"error": "internal_error", "detail": str(exc)})
        return JSONResponse(status_code=500, content={"error": "internal_error"})

    return app


app = create_app()