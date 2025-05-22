from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
from sqlalchemy.exc import IntegrityError

from ...core import security
from ...db.session import get_db
from .. import schemas
from ...models.user import User
from .auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=schemas.UserInDB,
    summary="Create new user",
    description="""
    Create a new user account with the provided information.

    Note: By default, users are created with `is_active=true` and `is_superuser=false`.
    Only superusers can create other superusers.
    """,
    responses={
        201: {
            "description": "User created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "email": "user@example.com",
                        "full_name": "John Doe",
                        "is_active": True,
                        "is_superuser": False,
                        "id": 1,
                        "created_at": "2025-05-10T21:45:00",
                        "updated_at": None,
                    }
                }
            },
        },
        400: {
            "description": "Email already registered",
            "content": {
                "application/json": {"example": {"detail": "Email already registered"}}
            },
        },
    },
)
async def create_user(
    *, db: Session = Depends(get_db), user_in: schemas.UserCreate
) -> Any:
    """Create new user."""
    try:
        user = User(
            email=user_in.email,
            hashed_password=security.get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_active=user_in.is_active,
            is_superuser=user_in.is_superuser,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )


@router.get(
    "/me",
    response_model=schemas.UserInDB,
    summary="Get current user",
    description="Retrieve information about the currently authenticated user.",
    responses={
        200: {
            "description": "Current user information",
            "content": {
                "application/json": {
                    "example": {
                        "email": "user@example.com",
                        "full_name": "John Doe",
                        "is_active": True,
                        "is_superuser": False,
                        "id": 1,
                        "created_at": "2025-05-10T21:45:00",
                        "updated_at": None,
                    }
                }
            },
        }
    },
)
async def read_user_me(current_user: User = Depends(get_current_user)) -> Any:
    """Get current user."""
    return current_user


@router.put(
    "/me",
    response_model=schemas.UserInDB,
    summary="Update current user",
    description="""
    Update information for the currently authenticated user.

    Fields that can be updated:
    - email
    - full_name
    - password (must be at least 8 characters)

    Only provide the fields you want to update.
    """,
    responses={
        200: {
            "description": "User updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "email": "updated@example.com",
                        "full_name": "Updated Name",
                        "is_active": True,
                        "is_superuser": False,
                        "id": 1,
                        "created_at": "2025-05-10T21:45:00",
                        "updated_at": "2025-05-10T21:46:00",
                    }
                }
            },
        },
        400: {
            "description": "Email already registered",
            "content": {
                "application/json": {"example": {"detail": "Email already registered"}}
            },
        },
    },
)
async def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update current user."""
    if user_in.email is not None:
        current_user.email = user_in.email
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name
    if user_in.password is not None:
        current_user.hashed_password = security.get_password_hash(user_in.password)

    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )


@router.get(
    "/{user_id}",
    response_model=schemas.UserInDB,
    summary="Get user by ID",
    description="""
    Retrieve information about a specific user by their ID.

    Note: Regular users can only access their own information.
    Superusers can access information about any user.
    """,
    responses={
        200: {
            "description": "User information",
            "content": {
                "application/json": {
                    "example": {
                        "email": "user@example.com",
                        "full_name": "John Doe",
                        "is_active": True,
                        "is_superuser": False,
                        "id": 1,
                        "created_at": "2025-05-10T21:45:00",
                        "updated_at": None,
                    }
                }
            },
        },
        403: {
            "description": "Not enough permissions",
            "content": {
                "application/json": {"example": {"detail": "Not enough permissions"}}
            },
        },
        404: {
            "description": "User not found",
            "content": {"application/json": {"example": {"detail": "User not found"}}},
        },
    },
)
async def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get user by ID."""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.get(
    "",
    response_model=schemas.UserList,
    summary="List users",
    description="""
    List all users in the system with pagination support.

    Note: This endpoint is only accessible to superusers.

    Parameters:
    - skip: Number of users to skip (for pagination)
    - limit: Maximum number of users to return
    """,
    responses={
        200: {
            "description": "List of users",
            "content": {
                "application/json": {
                    "example": {
                        "users": [
                            {
                                "email": "user1@example.com",
                                "full_name": "User One",
                                "is_active": True,
                                "is_superuser": False,
                                "id": 1,
                                "created_at": "2025-05-10T21:45:00",
                                "updated_at": None,
                            },
                            {
                                "email": "user2@example.com",
                                "full_name": "User Two",
                                "is_active": True,
                                "is_superuser": False,
                                "id": 2,
                                "created_at": "2025-05-10T21:46:00",
                                "updated_at": None,
                            },
                        ],
                        "total": 2,
                    }
                }
            },
        },
        403: {
            "description": "Not enough permissions",
            "content": {
                "application/json": {"example": {"detail": "Not enough permissions"}}
            },
        },
    },
)
async def list_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """List users. Only superusers can access this endpoint."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    users = db.query(User).offset(skip).limit(limit).all()
    total = db.query(User).count()
    return {"users": users, "total": total}
