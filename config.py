import os
from dotenv import load_dotenv

load_dotenv()


def get_database_uri():
    # Railway provides DATABASE_URL for the Postgres service.
    # Locally it's absent, so we fall back to SQLite.
    url = os.getenv("DATABASE_URL")

    if url:
        # SQLAlchemy needs the "postgresql://" scheme, but Railway
        # (and some providers) hand out "postgres://". Fix the prefix.
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # No DATABASE_URL → we're on the laptop → keep using local SQLite.
    return "sqlite:///mate.db"


class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = get_database_uri()