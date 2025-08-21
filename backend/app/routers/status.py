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
        "environment": cfg.app.env,
        "model_endpoint": cfg.ai_model.endpoint if cfg.app.env == "prod" else "local_vllm"
    }

@router.get("/health")
async def health_check(cfg: DictConfig = Depends(get_config)):
    """
    Checks the health of the application and its dependencies.
    """
    # Check AI model status based on environment
    if cfg.app.env == "prod":
        # Production: Check external AI model endpoint
        try:
            async with httpx.AsyncClient(timeout=cfg.ai_model.health_check_timeout_seconds) as client:
                response = await client.get(cfg.ai_model.endpoint)
                model_status = "ok" if response.status_code == 200 else "error"
        except httpx.RequestError:
            model_status = "error"
    else:
        # Development: Check local vLLM model availability
        try:
            from app.llm_client import vllm_model
            model_status = "ok" if vllm_model is not None else "error"
        except Exception:
            model_status = "error"

    return {
        "status": "ok",
        "dependencies": {
            "ai_model": model_status,
        },
    } 