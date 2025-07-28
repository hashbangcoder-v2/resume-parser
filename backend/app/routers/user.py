from fastapi import APIRouter
from app import schemas

router = APIRouter(
    prefix="/api/user",
    tags=["user"],
)

@router.get("/", response_model=schemas.Candidate)
def get_user():
    # This is mock data, in a real application you would get the logged in user
    return {"id": 99, "name": "Sarah Johnson", "email": "sarah.johnson@company.com", "created_at": "2024-01-01T12:00:00"} 