from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from trendscout.core.config import settings  # Import application settings
from trendscout.db.base_class import Base
from trendscout.db.session import get_db
from trendscout.main import app

# Use the database URL from application settings (which will be PostgreSQL in CI)
SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
    # For PostgreSQL, connect_args={"check_same_thread": False} is not needed and invalid.
    # poolclass=StaticPool might also be removed or changed for PostgreSQL if necessary,
    # but default pooling is usually fine for tests.
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables. This will now run against the PostgreSQL test database in CI.
# Note: Alembic migrations should ideally handle table creation.
# If Alembic is already creating tables, this line might be redundant or even
# cause issues if it tries to recreate tables. For now, we keep it to match
# the original structure, but this is a point of attention.
# If tests fail due to "table already exists", consider removing this.
# However, for a clean test DB per session/module, it's often needed if not using migrations for setup.
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def db() -> Generator[Session, None, None]:
    """Fixture that returns a SQLAlchemy session for testing."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Fixture that returns a TestClient for testing API endpoints."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user():
    """Fixture that returns test user data."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }


@pytest.fixture
def test_superuser():
    """Fixture that returns test superuser data."""
    return {
        "email": "admin@example.com",
        "password": "adminpassword123",
        "full_name": "Admin User",
        "is_superuser": True,
    }


@pytest.fixture
def test_task():
    """Fixture that returns test task data."""
    return {
        "title": "Test Task",
        "description": "Test task description",
        "task_type": "trend_analysis",
        "status": "pending",
    }
