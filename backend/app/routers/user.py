from fastapi import APIRouter
from app import schemas
from app.logger import logger
router = APIRouter(
    prefix="/api/user",
    tags=["user"],
)

@router.get("", response_model=schemas.Candidate)
def get_user():
    logger.info("Getting user")
    # This is mock data, in a real application you would get the logged in user
    return {"id": 99, "name": "Sarah Johnson", "email": "sarah.johnson@company.com", "created_at": "2024-01-01T12:00:00"} 