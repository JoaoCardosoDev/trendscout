from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from trendscout.core.security import create_access_token
from trendscout.models.user import User


def test_create_user(client: TestClient, test_user: Dict[str, str]) -> None:
    """Test user creation endpoint."""
    data = {
        "email": test_user["email"],
        "password": test_user["password"],
        "full_name": test_user["full_name"],
    }
    response = client.post("/users/", json=data)
    result = response.json()

    assert response.status_code == 200
    assert result["email"] == test_user["email"]
    assert result["full_name"] == test_user["full_name"]
    assert "id" in result
    assert "password" not in result


def test_create_user_existing_email(
    client: TestClient, test_user: Dict[str, str], db: Session
) -> None:
    """Test user creation with existing email."""
    # Create a user first
    user = User(
        email=test_user["email"],
        hashed_password=test_user["password"],
        full_name=test_user["full_name"],
    )
    db.add(user)
    db.commit()

    # Try to create another user with same email
    data = {
        "email": test_user["email"],
        "password": "different_password",
        "full_name": "Different Name",
    }
    response = client.post("/users/", json=data)

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_read_users_me(
    client: TestClient, test_user: Dict[str, str], db: Session
) -> None:
    """Test getting current user info."""
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

    response = client.get("/users/me", headers=headers)
    result = response.json()

    assert response.status_code == 200
    assert result["email"] == test_user["email"]
    assert result["full_name"] == test_user["full_name"]
    assert "id" in result


def test_read_users_me_no_auth(client: TestClient) -> None:
    """Test getting current user info without authentication."""
    response = client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_update_user_me(
    client: TestClient, test_user: Dict[str, str], db: Session
) -> None:
    """Test updating current user info."""
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

    data = {"full_name": "Updated Name"}
    response = client.put("/users/me", headers=headers, json=data)
    result = response.json()

    assert response.status_code == 200
    assert result["email"] == test_user["email"]
    assert result["full_name"] == "Updated Name"


def test_read_user_by_id(
    client: TestClient,
    test_superuser: Dict[str, str],
    test_user: Dict[str, str],
    db: Session,
) -> None:
    """Test getting user by ID (superuser only)."""
    # Create superuser
    superuser = User(
        email=test_superuser["email"],
        hashed_password=test_superuser["password"],
        full_name=test_superuser["full_name"],
        is_superuser=True,
    )
    db.add(superuser)

    # Create normal user
    user = User(
        email=test_user["email"],
        hashed_password=test_user["password"],
        full_name=test_user["full_name"],
    )
    db.add(user)
    db.commit()

    access_token = create_access_token(subject=superuser.email)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get(f"/users/{user.id}", headers=headers)
    result = response.json()

    assert response.status_code == 200
    assert result["email"] == test_user["email"]
    assert result["full_name"] == test_user["full_name"]
    assert result["id"] == user.id


def test_read_user_by_id_normal_user(
    client: TestClient, test_user: Dict[str, str], db: Session
) -> None:
    """Test getting user by ID with normal user (should fail)."""
    # Create users
    user1 = User(
        email=test_user["email"],
        hashed_password=test_user["password"],
        full_name=test_user["full_name"],
    )
    db.add(user1)

    user2 = User(
        email="other@example.com",
        hashed_password="password123",
        full_name="Other User",
    )
    db.add(user2)
    db.commit()

    access_token = create_access_token(subject=user1.email)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get(f"/users/{user2.id}", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"
