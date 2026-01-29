from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LTC_", case_sensitive=False)

    env: str = "dev"  # dev | prod | test
    secret_key: str | None = None  # Pflicht (JWT Signatur)
    jwt_algorithm: str = "HS256"

    database_url: str = "sqlite+pysqlite:///./data/app.db"


@lru_cache
def get_settings() -> Settings:
    s = Settings()

    # deny-by-default: ohne SECRET_KEY keine API
    if not s.secret_key:
        raise RuntimeError("LTC_SECRET_KEY fehlt (Pflicht).")

    return s
