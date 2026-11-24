"""Shared fixtures for isolated backend API tests."""

import os

import pytest
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models import Base
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture
def db_session():
    """Create a fresh SQLite database for each test."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection,
        connection_record,
    ):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        yield session

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db_session):
    """Create a test client using the isolated database."""

    previous_overrides = app.dependency_overrides.copy()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


@pytest.fixture(scope="module")
def analytics_test_engine():
    """Create an isolated PostgreSQL engine for analytics API tests.

    TEST_DATABASE_URL must point to a dedicated test database.
    The fixture creates and removes its schema.
    """

    database_url = os.getenv("TEST_DATABASE_URL")

    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL analytics tests.")

    test_url = make_url(database_url)
    application_url = make_url(settings.database_url)

    if not test_url.drivername.startswith("postgresql"):
        raise RuntimeError("Analytics integration tests require PostgreSQL.")

    if (
        test_url.host,
        test_url.port,
        test_url.database,
    ) == (
        application_url.host,
        application_url.port,
        application_url.database,
    ):
        raise RuntimeError(
            "Analytics tests cannot use the application database. "
            "Configure a separate TEST_DATABASE_URL."
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def analytics_test_session(analytics_test_engine):
    """Give each analytics test an outer transaction.

    API commits are contained in savepoints. The outer transaction
    is rolled back after each test.
    """

    connection = analytics_test_engine.connect()
    outer_transaction = connection.begin()

    session = Session(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()

        if outer_transaction.is_active:
            outer_transaction.rollback()

        connection.close()


@pytest.fixture
def analytics_client(analytics_test_session):
    """Test analytics endpoints against isolated PostgreSQL."""

    previous_overrides = app.dependency_overrides.copy()

    def override_get_db():
        yield analytics_test_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
