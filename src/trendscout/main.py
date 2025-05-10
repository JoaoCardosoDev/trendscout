from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .core.config import get_settings
from .core.logging import RequestContextMiddleware, log_request, log_error, logger
from .db.session import get_db
from .db.init_db import init_db
from .api import api_router

settings = get_settings()

tags_metadata = [
    {
        "name": "auth",
        "description": "Authentication operations. Use these endpoints to obtain and manage access tokens.",
        "externalDocs": {
            "description": "Auth Flow Documentation",
            "url": "/docs#section/Authentication",
        },
    },
    {
        "name": "users",
        "description": "Operations with users. Create and manage user accounts.",
    },
    {
        "name": "tasks",
        "description": """
        Agent task operations. Create and manage AI agent tasks for:
        * Trend Analysis - Identify trending topics from platforms like Twitter and Reddit
        * Content Generation - Generate creative post ideas based on trends
        * Scheduling - Determine optimal publishing times for content
        """,
    },
]

description = """
# Trendscout API

AI-powered trend analysis and content generation system that helps you stay ahead of the curve.

## Key Features

* **🔍 Trend Analysis**: Automatically identify trending topics from social media platforms
* **✍️ Content Generation**: Get AI-generated post ideas based on current trends
* **⏰ Scheduling**: Optimize your content publishing times for maximum engagement
* **🔐 Authentication**: Secure JWT-based authentication system
* **📊 Task Management**: Track and manage your AI agent tasks

## Authentication

All API endpoints (except /auth/login) require a valid JWT token. To authenticate:

1. Use the `/auth/login` endpoint with your email and password
2. Include the returned token in the Authorization header:
   ```
   Authorization: Bearer <your_token>
   ```

## Agent Types

The system supports three types of AI agents:

* `trend_analyzer`: Analyzes social media platforms to identify trending topics
* `content_generator`: Creates engaging post ideas based on trends
* `scheduler`: Determines optimal publishing times based on engagement patterns

Each agent is accessed through the tasks endpoints, with specific input requirements detailed in the task creation documentation.
"""

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=description,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Add logging middleware
app.add_middleware(RequestContextMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests and responses."""
    try:
        log_request(request)
        response = await call_next(request)
        return response
    except Exception as e:
        log_error(e, request)
        raise

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check(request: Request, db: Session = Depends(get_db)):
    """Health check endpoint that verifies database connection."""
    try:
        # Try to make a simple database query
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        log_error(e, request)
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
