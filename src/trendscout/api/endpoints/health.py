from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Health check endpoint.
    Returns a status of "ok" if the service is running.
    """
    return {"status": "ok"}
