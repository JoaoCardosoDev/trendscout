from fastapi import APIRouter

from trendscout.api.endpoints import auth, users, tasks, health

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tasks.router, tags=["tasks"])  # Removed prefix="/tasks"
api_router.include_router(health.router, prefix="/health", tags=["health"])
