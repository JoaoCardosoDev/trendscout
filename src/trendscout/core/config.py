from typing import Optional, Dict, ClassVar
from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import field_validator
from .logging import logger

class MissingEnvironmentError(Exception):
    """Raised when required environment variables are missing."""
    pass

class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Required environment variables
    REQUIRED_VARS: ClassVar[Dict[str, str]] = {
        "SECRET_KEY": "JWT secret key",
        "POSTGRES_PASSWORD": "Database password",
        "POSTGRES_USER": "Database username",
        "POSTGRES_DB": "Database name",
        "POSTGRES_SERVER": "Database host",
        "POSTGRES_PORT": "Database port",
        "REDIS_HOST": "Redis host",
        "OLLAMA_BASE_URL": "Ollama API URL",
        "SUPERUSER_EMAIL": "Initial admin user email",
        "SUPERUSER_PASSWORD": "Initial admin user password"
    }
    
    # Base
    PROJECT_NAME: str = "Trendscout"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Superuser configuration
    SUPERUSER_EMAIL: str = "admin@example.com"
    SUPERUSER_PASSWORD: str = "admin"  # This should be changed in production
    
    # Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str
    
    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    
    # Ollama
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str = "llama2"  # Default model
    OLLAMA_TIMEOUT: int = 600  # 10 minutes timeout (increased from 300)
    OLLAMA_REQUEST_TIMEOUT: int = 300  # 1 minute timeout for requests
    
    # CORS
    BACKEND_CORS_ORIGINS: Optional[list[str]] = []
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Get the SQLAlchemy database URI."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @field_validator('*')
    @classmethod
    def check_required_vars(cls, v: str, info):
        """Validate that required environment variables are set and not empty."""
        if info.field_name in cls.REQUIRED_VARS and (v is None or v == ""):
            raise MissingEnvironmentError(
                f"Missing required environment variable: {info.field_name} ({cls.REQUIRED_VARS[info.field_name]})"
            )
        return v

    def validate_all(self):
        """Validate all required environment variables are properly set."""
        missing_vars = []
        for var_name, var_desc in self.REQUIRED_VARS.items():
            value = getattr(self, var_name, None)
            if value is None or value == "":
                missing_vars.append(f"{var_name} ({var_desc})")
        
        if missing_vars:
            error_msg = "Missing required environment variables:\n" + "\n".join(missing_vars)
            logger.error(error_msg)
            raise MissingEnvironmentError(error_msg)
        
        logger.info("All required environment variables are set")
        return True

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "validate_default_values": True
    }

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance with validation."""
    settings = Settings()
    settings.validate_all()
    return settings

settings = get_settings()
