from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthSettings:
    # HMAC Key (min. 32 Zeichen) – bereits im Projekt als LTC_SECRET_KEY genutzt
    secret_key: str

    # SQLite DB (default: server/data/app.db)
    db_path: str

    # OTP / Session TTLs
    otp_ttl_seconds: int = 10 * 60            # 10 Minuten
    session_ttl_seconds: int = 24 * 60 * 60   # 24h

    # Rate Limits (pro Fenster)
    rl_window_seconds: int = 10 * 60          # 10 Minuten
    rl_req_per_email: int = 5                # /auth/request pro email_hmac
    rl_req_per_ip: int = 20                  # /auth/request pro ip_hmac
    rl_verify_per_ip: int = 30               # /auth/verify pro ip_hmac

    # Dev: OTP im Response ausgeben (NUR lokal)
    dev_expose_otp: bool = False

    # Consent (AGB/Datenschutz) – REQUIRED Versions (serverseitig enforced)
    terms_version_required: str = "v1"
    privacy_version_required: str = "v1"

    # Mailer
    mailer_mode: str = "null"                 # null|smtp

    # SMTP (nur nötig wenn mailer_mode=smtp)
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_pass: str | None = None
    smtp_from: str | None = None
    smtp_starttls: bool = True


def load_settings() -> AuthSettings:
    secret = (os.getenv("LTC_SECRET_KEY") or "").strip()
    if len(secret) < 32:
        raise RuntimeError("LTC_SECRET_KEY fehlt/zu kurz (mind. 32 Zeichen).")

    db_path = (os.getenv("LTC_DB_PATH") or "").strip()
    if not db_path:
        db_path = "./data/app.db"

    dev_flag = (os.getenv("LTC_DEV_EXPOSE_OTP") or "").strip().lower() in ("1", "true", "yes", "on")

    # Consent required versions (Defaults v1)
    terms_v = (os.getenv("LTC_TERMS_VERSION") or "v1").strip()
    privacy_v = (os.getenv("LTC_PRIVACY_VERSION") or "v1").strip()

    mailer_mode = (os.getenv("LTC_MAILER_MODE") or "null").strip().lower()

    smtp_host = (os.getenv("LTC_SMTP_HOST") or "").strip() or None
    smtp_port_raw = (os.getenv("LTC_SMTP_PORT") or "").strip()
    smtp_port = int(smtp_port_raw) if smtp_port_raw.isdigit() else None

    smtp_user = (os.getenv("LTC_SMTP_USER") or "").strip() or None
    smtp_pass = (os.getenv("LTC_SMTP_PASS") or "").strip() or None
    smtp_from = (os.getenv("LTC_SMTP_FROM") or "").strip() or None

    smtp_starttls = (os.getenv("LTC_SMTP_STARTTLS") or "true").strip().lower() in ("1", "true", "yes", "on")

    return AuthSettings(
        secret_key=secret,
        db_path=db_path,
        dev_expose_otp=dev_flag,
        terms_version_required=terms_v,
        privacy_version_required=privacy_v,
        mailer_mode=mailer_mode,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_pass=smtp_pass,
        smtp_from=smtp_from,
        smtp_starttls=smtp_starttls,
    )
