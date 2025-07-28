from fastapi import APIRouter, Depends
from omegaconf import DictConfig
from app.config import get_config
import logging
import httpx

# Use a structured logger
logging.basicConfig(level=logging.INFO) # Changed to INFO as per new_code
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["status"],
)

@router.get("/status")
def get_status(cfg: DictConfig = Depends(get_config)):
    return {
        "status": "ok",
        "model_endpoint": cfg.ai_model.endpoint
    }

@router.get("/health")
async def health_check(cfg: DictConfig = Depends(get_config)):
    """
    Checks the health of the application and its dependencies.
    """
    # Check the status of the AI model endpoint
    try:
        async with httpx.AsyncClient(timeout=cfg.ai_model.health_check_timeout_seconds) as client:
            response = await client.get(cfg.ai_model.endpoint)
            # A more robust check might be needed depending on the model server's health endpoint
            if response.status_code == 200:
                model_status = "ok"
            else:
                model_status = "error"
    except httpx.RequestError:
        model_status = "error"

    return {
        "status": "ok",
        "dependencies": {
            "ai_model": model_status,
        },
    } 