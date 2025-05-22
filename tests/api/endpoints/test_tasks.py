from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from trendscout.core.security import create_access_token
from trendscout.models.task import Task
from trendscout.models.user import User


def test_create_task(
    client: TestClient,
    test_user: Dict[str, str],
    test_task: Dict[str, str],
    db: Session,
) -> None:
    """Test task creation endpoint."""
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

    response = client.post("/tasks/", headers=headers, json=test_task)
    result = response.json()

    assert response.status_code == 200
    assert result["title"] == test_task["title"]
    assert result["description"] == test_task["description"]
    assert result["task_type"] == test_task["task_type"]
    assert result["status"] == "pending"
    assert "id" in result
    assert "created_at" in result


def test_create_task_no_auth(client: TestClient, test_task: Dict[str, str]) -> None:
    """Test task creation without authentication."""
    response = client.post("/tasks/", json=test_task)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_read_task(
    client: TestClient,
    test_user: Dict[str, str],
    test_task: Dict[str, str],
    db: Session,
) -> None:
    """Test getting task by ID."""
    # Create a user
    user = User(
        email=test_user["email"],
        hashed_password=test_user["password"],
        full_name=test_user["full_name"],
    )
    db.add(user)
    db.commit()

    # Create a task
    task = Task(
        title=test_task["title"],
        description=test_task["description"],
        task_type=test_task["task_type"],
        status=test_task["status"],
        owner_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    access_token = create_access_token(subject=user.email)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get(f"/tasks/{task.id}", headers=headers)
    result = response.json()

    assert response.status_code == 200
    assert result["title"] == test_task["title"]
    assert result["description"] == test_task["description"]
    assert result["id"] == task.id


def test_read_task_not_found(
    client: TestClient, test_user: Dict[str, str], db: Session
) -> None:
    """Test getting non-existent task."""
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

    response = client.get("/tasks/999", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_read_tasks(
    client: TestClient,
    test_user: Dict[str, str],
    test_task: Dict[str, str],
    db: Session,
) -> None:
    """Test getting list of user's tasks."""
    # Create a user
    user = User(
        email=test_user["email"],
        hashed_password=test_user["password"],
        full_name=test_user["full_name"],
    )
    db.add(user)
    db.commit()

    # Create multiple tasks
    tasks = [
        Task(
            title=f"{test_task['title']} {i}",
            description=test_task["description"],
            task_type=test_task["task_type"],
            status=test_task["status"],
            owner_id=user.id,
        )
        for i in range(3)
    ]
    db.add_all(tasks)
    db.commit()

    access_token = create_access_token(subject=user.email)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get("/tasks/", headers=headers)
    results = response.json()

    assert response.status_code == 200
    assert len(results) == 3
    for i, result in enumerate(results):
        assert result["title"] == f"{test_task['title']} {i}"
        assert result["description"] == test_task["description"]
        assert "id" in result


def test_update_task_status(
    client: TestClient,
    test_user: Dict[str, str],
    test_task: Dict[str, str],
    db: Session,
) -> None:
    """Test updating task status."""
    # Create a user
    user = User(
        email=test_user["email"],
        hashed_password=test_user["password"],
        full_name=test_user["full_name"],
    )
    db.add(user)
    db.commit()

    # Create a task
    task = Task(
        title=test_task["title"],
        description=test_task["description"],
        task_type=test_task["task_type"],
        status="pending",
        owner_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    access_token = create_access_token(subject=user.email)
    headers = {"Authorization": f"Bearer {access_token}"}

    update_data = {"status": "completed"}
    response = client.patch(f"/tasks/{task.id}", headers=headers, json=update_data)
    result = response.json()

    assert response.status_code == 200
    assert result["status"] == "completed"
    assert result["id"] == task.id


def test_delete_task(
    client: TestClient,
    test_user: Dict[str, str],
    test_task: Dict[str, str],
    db: Session,
) -> None:
    """Test task deletion."""
    # Create a user
    user = User(
        email=test_user["email"],
        hashed_password=test_user["password"],
        full_name=test_user["full_name"],
    )
    db.add(user)
    db.commit()

    # Create a task
    task = Task(
        title=test_task["title"],
        description=test_task["description"],
        task_type=test_task["task_type"],
        status=test_task["status"],
        owner_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    access_token = create_access_token(subject=user.email)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.delete(f"/tasks/{task.id}", headers=headers)
    assert response.status_code == 200

    # Verify task is deleted
    response = client.get(f"/tasks/{task.id}", headers=headers)
    assert response.status_code == 404
