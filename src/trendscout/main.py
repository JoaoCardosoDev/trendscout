from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .core.config import get_settings
from .core.logging import RequestContextMiddleware, log_request, log_error, logger
from .db.session import get_db
from .db.init_db import init_db
from .api import api_router

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered trend analysis and content generation system",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
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
