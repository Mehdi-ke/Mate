import os

from dotenv import load_dotenv

load_dotenv()


def get_database_uri(default="sqlite:///mate.db"):
    """Return a SQLAlchemy-compatible database URL from the environment."""
    url = os.getenv("DATABASE_URL")
    if not url:
        return default
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_TIME_LIMIT = 3600


class DevelopmentConfig(Config):
    DEBUG = True


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key-only"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestConfig,
    "production": ProductionConfig,
}
