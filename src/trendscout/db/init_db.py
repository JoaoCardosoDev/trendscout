from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .base_class import Base
from .session import engine, SessionLocal
from ..models.user import User
from ..models.task import AgentTask
from ..core.config import get_settings
from ..core.logging import logger


def init_db() -> None:
    """Initialize the database with required tables."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully (if they didn't exist).")
    except SQLAlchemyError as e:
        logger.error(f"Error initializing database tables: {str(e)}")
        raise


def create_superuser(db: Session) -> None:
    """Create a superuser if it doesn't exist."""
    settings = get_settings()

    try:
        # Check if superuser exists
        superuser = db.query(User).filter(User.is_superuser == True).first()
        if not superuser:
            from ..core.security import get_password_hash

            # Get superuser credentials from environment or use defaults
            email = settings.SUPERUSER_EMAIL or "admin@example.com"
            password = settings.SUPERUSER_PASSWORD or "admin"

            superuser = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name="System Admin",
                is_superuser=True,
            )
            db.add(superuser)
            db.commit()
            logger.info(f"Created superuser with email: {email}")
        else:
            logger.info("Superuser already exists")

    except SQLAlchemyError as e:
        logger.error(f"Error creating superuser: {str(e)}")
        db.rollback()
        raise


def ensure_database_state():
    """Ensure database is initialized and superuser exists."""
    try:
        # Initialize database
        init_db()

        # Create superuser using a new session
        with SessionLocal() as db:
            create_superuser(db)

        logger.info("Database state verification completed successfully")
    except Exception as e:
        logger.error(f"Error ensuring database state: {str(e)}")
        raise
