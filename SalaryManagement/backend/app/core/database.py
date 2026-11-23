
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


# SQLAlchemy database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


# Creates independent database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Provides a database session to API endpoints.

    The session is always closed after the request,
    even when an exception occurs.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
