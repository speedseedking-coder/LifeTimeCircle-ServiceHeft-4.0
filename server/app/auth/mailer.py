from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol, Optional

from .settings import AuthSettings


class Mailer(Protocol):
    def send_login_otp(self, *, to_email: str, otp: str, challenge_id: str) -> None:
        """
        Sendet OTP an echte Mailadresse.
        WICHTIG: Keine Logs, keine Persistenz, kein Klartext-OTP irgendwo speichern.
        """
        ...


@dataclass(frozen=True)
class NullMailer:
    """
    Stub: macht nichts (prod-sicher, aber kein Versand).
    """
    def send_login_otp(self, *, to_email: str, otp: str, challenge_id: str) -> None:
        return


@dataclass(frozen=True)
class SmtpMailer:
    host: str
    port: int
    username: Optional[str]
    password: Optional[str]
    mail_from: str
    starttls: bool = True

    def send_login_otp(self, *, to_email: str, otp: str, challenge_id: str) -> None:
        # Keine Logs. E-Mail Body enthält OTP (ist der Zweck).
        msg = EmailMessage()
        msg["Subject"] = "LifeTimeCircle – Login-Code"
        msg["From"] = self.mail_from
        msg["To"] = to_email

        msg.set_content(
            "\n".join(
                [
                    "Dein Login-Code:",
                    otp,
                    "",
                    "Wenn du das nicht angefordert hast: ignorieren.",
                    "",
                    f"Referenz: {challenge_id}",
                ]
            )
        )

        with smtplib.SMTP(self.host, self.port, timeout=20) as server:
            if self.starttls:
                server.starttls()

            if self.username and self.password:
                server.login(self.username, self.password)

            server.send_message(msg)


def get_mailer(settings: AuthSettings) -> Mailer:
    mode = (settings.mailer_mode or "null").strip().lower()

    if mode == "null":
        return NullMailer()

    if mode == "smtp":
        # SMTP-Config muss gesetzt sein
        if not settings.smtp_host:
            raise RuntimeError("SMTP aktiviert, aber LTC_SMTP_HOST fehlt.")
        if not settings.smtp_from:
            raise RuntimeError("SMTP aktiviert, aber LTC_SMTP_FROM fehlt.")
        return SmtpMailer(
            host=settings.smtp_host,
            port=int(settings.smtp_port or 587),
            username=settings.smtp_user,
            password=settings.smtp_pass,
            mail_from=settings.smtp_from,
            starttls=bool(settings.smtp_starttls),
        )

    raise RuntimeError(f"Unbekannter Mailer-Mode: {mode} (erlaubt: null|smtp)")
