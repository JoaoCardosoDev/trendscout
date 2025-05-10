from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from trendscout.core.security import create_access_token
from trendscout.models.user import User


def test_login_success(client: TestClient, test_user: Dict[str, str], db: Session) -> None:
    """Test successful login."""
    # Create a user
    user = User(
        email=test_user["email"],
        hashed_password=test_user["password"],  # In real app this would be hashed
        full_name=test_user["full_name"],
    )
    db.add(user)
    db.commit()

    data = {
        "username": test_user["email"],
        "password": test_user["password"],
    }
    response = client.post("/auth/login", data=data)
    tokens = response.json()

    assert response.status_code == 200
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_login_incorrect_password(client: TestClient, test_user: Dict[str, str], db: Session) -> None:
    """Test login with incorrect password."""
    # Create a user
    user = User(
        email=test_user["email"],
        hashed_password=test_user["password"],
        full_name=test_user["full_name"],
    )
    db.add(user)
    db.commit()

    data = {
        "username": test_user["email"],
        "password": "wrongpassword",
    }
    response = client.post("/auth/login", data=data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_nonexistent_user(client: TestClient) -> None:
    """Test login with non-existent user."""
    data = {
        "username": "nonexistent@example.com",
        "password": "password123",
    }
    response = client.post("/auth/login", data=data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_test_token(
    client: TestClient, test_user: Dict[str, str], db: Session
) -> None:
    """Test token validation endpoint."""
    # Create a user
    user = User(
        email=test_user["email"],
        hashed_password=test_user["password"],
        full_name=test_user["full_name"],
    )
    db.add(user)
    db.commit()

    access_token = create_access_token(subject=user.email)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = client.post("/auth/test-token", headers=headers)
    
    assert response.status_code == 200
    result = response.json()
    assert result["email"] == test_user["email"]


def test_test_token_invalid(client: TestClient) -> None:
    """Test token validation with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.post("/auth/test-token", headers=headers)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
