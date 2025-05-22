from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path

from trendscout.core.config import settings
from trendscout.api.api_v1.api import api_router
from trendscout.db.session import SessionLocal
from trendscout.db import base_class # noqa: F401
from trendscout.db import init_db

# Logging is initialized automatically upon import of trendscout.core.logging

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/trendscout/static"), name="static")

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.on_event("startup")
def on_startup():
    # db = SessionLocal() # Not needed here as init_db doesn't take db session
    init_db.init_db() # Corrected: init_db takes no arguments
    # db.close() # Not needed here

# UPDATED ROUTER INCLUSION:
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = Path("src/trendscout/static/index.html").read_text()
    return HTMLResponse(content=html_content)

@app.get("/ui", response_class=HTMLResponse)
async def read_ui():
    html_content = Path("src/trendscout/static/index.html").read_text()
    return HTMLResponse(content=html_content)

@app.get("/ui/{catchall:path}", response_class=HTMLResponse)
async def read_ui_catchall(catchall: str):
    html_content = Path("src/trendscout/static/index.html").read_text()
    return HTMLResponse(content=html_content)
