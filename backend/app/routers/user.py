from fastapi import APIRouter
from app import schemas
from app.logger import logger
router = APIRouter(
    prefix="/api/user",
    tags=["user"],
)

@router.get("", response_model=schemas.Candidate)
def get_user():
    logger.info("Getting logged in user")    
    return {"id": 0, "name": "Mock User", "email": "mock.user@qwerty.com", "created_at": "2024-01-01T12:00:00"} 