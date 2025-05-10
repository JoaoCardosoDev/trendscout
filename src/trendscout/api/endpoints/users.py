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

@router.post("", response_model=schemas.UserInDB)
async def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate
) -> Any:
    """Create new user."""
    try:
        user = User(
            email=user_in.email,
            hashed_password=security.get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_active=user_in.is_active,
            is_superuser=user_in.is_superuser
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

@router.get("/me", response_model=schemas.UserInDB)
async def read_user_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current user."""
    return current_user

@router.put("/me", response_model=schemas.UserInDB)
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

@router.get("/{user_id}", response_model=schemas.UserInDB)
async def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get user by ID."""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("", response_model=schemas.UserList)
async def list_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """List users. Only superusers can access this endpoint."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    users = db.query(User).offset(skip).limit(limit).all()
    total = db.query(User).count()
    return {"users": users, "total": total}
