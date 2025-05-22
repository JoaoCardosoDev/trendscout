from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from trendscout.db.base_class import Base
from trendscout.db.session import get_db
from trendscout.main import app

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables for each test
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
