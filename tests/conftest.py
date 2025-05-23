from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from trendscout.core.config import settings
from trendscout.db.base_class import Base
from trendscout.db.session import get_db
from trendscout.main import app

SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=(
        {"client_encoding": "utf8"} if "postgresql" in SQLALCHEMY_DATABASE_URL else {}
    ),
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """
    Create all tables once per test session.
    """
    Base.metadata.create_all(bind=engine)
    yield
    # Optionally, drop tables after session, but usually not needed if DB is ephemeral
    # Base.metadata.drop_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Fixture that returns a SQLAlchemy session for testing.
    Data is cleared from all tables before each test.
    A transaction is started before the test and rolled back after.
    """
    connection = engine.connect()
    # Begin a non-ORM transaction
    transaction = connection.begin()
    # Bind an ORM session to the connection
    session = TestingSessionLocal(bind=connection)

    # Clear data from all tables before each test
    # Iterate in reverse to handle foreign key constraints
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()  # Commit the deletions

    yield session

    session.close()
    # Rollback the overall transaction
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")  # Changed scope to function
def client(
    db: Session,
) -> Generator[TestClient, None, None]:  # Added db: Session dependency to signature
    """Fixture that returns a TestClient for testing API endpoints."""
    # app.dependency_overrides[get_db] = override_get_db is set globally when conftest is imported.
    # The db fixture will be available to tests that request it.
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
