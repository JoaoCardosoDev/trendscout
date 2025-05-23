from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from trendscout.core.security import get_password_hash  # Import get_password_hash
from trendscout.models.user import User

# from trendscout.api import schemas


def test_login_incorrect_password(
    client: TestClient, test_user: Dict[str, str], db: Session
) -> None:
    """Test login with incorrect password."""
    hashed_password = get_password_hash("correct_password")
    user = User(
        email=test_user["email"],
        hashed_password=hashed_password,
        full_name=test_user["full_name"],
        is_active=True,
    )
    db.add(user)
    db.commit()

    login_data = {"username": test_user["email"], "password": "wrong_password"}
    response = client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
