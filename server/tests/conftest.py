import os

# LTC_TEST_SECRET_KEY_IMPORTTIME
import pytest

# LTC_TEST_SECRET_KEY_AUTOUSE
# Tests erwarten einen gültigen Secret-Key (>= 16 chars) für One-Time-Token Exporte.
# In Prod MUSS das aus Env/Secrets kommen – hier nur für Tests.
@pytest.fixture(autouse=True, scope="session")
def _ltc_test_secret_key() -> None:
    key = "test_secret_key__0123456789abcdef"
    os.environ.setdefault("LTC_SECRET_KEY", key)
    # optional Fallbacks, falls Settings andere Env-Namen akzeptieren:
    os.environ.setdefault("SECRET_KEY", key)
    os.environ.setdefault("APP_SECRET_KEY", key)
