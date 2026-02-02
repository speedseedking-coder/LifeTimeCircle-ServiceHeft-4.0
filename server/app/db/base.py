from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
from app.models.consent import ConsentAcceptance  # noqa: F401
