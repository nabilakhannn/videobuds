"""Flask application configuration."""

import logging
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

_DEFAULT_SECRET = "dev-secret-change-in-production"

logger = logging.getLogger(__name__)


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", _DEFAULT_SECRET)

    # Railway/Heroku set DATABASE_URL with postgres:// but SQLAlchemy
    # requires postgresql:// — fix it automatically.
    _db_url = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'videobuds.db'}")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB upload limit
    UPLOAD_FOLDER = str(BASE_DIR / "app" / "static" / "uploads")
    GENERATED_FOLDER = str(BASE_DIR / "app" / "static" / "generated")
    POSTHOG_API_KEY = os.environ.get("POSTHOG_API_KEY", "")
    POSTHOG_HOST = os.environ.get("POSTHOG_HOST", "https://app.posthog.com")

    # Input validation limits
    MAX_TEXT_INPUT_LENGTH = 500       # Single-line text fields
    MAX_TEXTAREA_INPUT_LENGTH = 5000  # Multi-line textarea fields

    # Recipe execution timeout (minutes) — runs exceeding this are reaped
    RECIPE_TIMEOUT_MINUTES = int(os.environ.get("RECIPE_TIMEOUT_MINUTES", "30"))


class DevelopmentConfig(Config):
    DEBUG = True

    def __init__(self):
        if self.SECRET_KEY == _DEFAULT_SECRET:
            logger.warning(
                "⚠️  Using default SECRET_KEY — set SECRET_KEY env var "
                "before deploying to production!"
            )


class ProductionConfig(Config):
    DEBUG = False

    def __init__(self):
        if self.SECRET_KEY == _DEFAULT_SECRET:
            raise RuntimeError(
                "FATAL: SECRET_KEY must be set via environment variable in "
                "production. Generate one with: python -c "
                "\"import secrets; print(secrets.token_hex(32))\""
            )


class TestingConfig(Config):
    """Configuration for automated tests.

    Uses an in-memory SQLite database with StaticPool to ensure all
    operations share the same connection (and thus the same database).
    Without StaticPool, each new connection gets a *separate* empty
    in-memory database — making tests appear to "lose" their data.
    """
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = True

    # StaticPool ensures every db.session operation reuses the same
    # connection, keeping the in-memory database alive for the full
    # test session.
    from sqlalchemy.pool import StaticPool  # noqa: E402
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
