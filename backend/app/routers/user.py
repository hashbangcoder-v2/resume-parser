from fastapi import APIRouter

router = APIRouter(
    prefix="/api/user",
    tags=["user"],
)

@router.get("/")
def get_user():
    return {"name": "John Doe", "email": "john.doe@example.com"} 