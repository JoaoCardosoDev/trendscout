from sqlalchemy.orm import Session

from .base_class import Base
from .session import engine
from ..models.user import User
from ..models.task import AgentTask
from ..core.config import get_settings

def init_db() -> None:
    """Initialize the database with required tables."""
    Base.metadata.create_all(bind=engine)

def create_superuser(db: Session) -> None:
    """Create a superuser if it doesn't exist."""
    settings = get_settings()
    
    # Check if superuser exists
    superuser = db.query(User).filter(User.is_superuser == True).first()
    if not superuser:
        from ..core.security import get_password_hash
        superuser = User(
            email="admin@example.com",  # Change in production
            hashed_password=get_password_hash("admin"),  # Change in production
            full_name="System Admin",
            is_superuser=True
        )
        db.add(superuser)
        db.commit()

def get_models():
    """Return all models for database operations."""
    return [User, AgentTask]
