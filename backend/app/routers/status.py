from fastapi import APIRouter
import httpx
from ..config import cfg
import logging

# Use a structured logger
logging.basicConfig(level=cfg.logging.level.upper())
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/status",
    tags=["status"],
)

@router.get("/")
async def get_status():
    """
    Checks the status of the backend and the configured AI model endpoint,
    and provides the recommended health check interval.
    """
    ai_model_status = "offline"
    endpoint = cfg.ai_model.endpoint
    timeout = cfg.ai_model.health_check_timeout_seconds

    try:
        async with httpx.AsyncClient() as client:
            if cfg.APP_ENV == "prod":
                # Azure ML endpoints often require a POST with sample data to check health
                # and don't typically support HEAD.
                sample_data = {"data": []}
                headers = {'Authorization': f'Bearer {cfg.azure_ml.api_key}'} if hasattr(cfg, 'azure_ml') else {}
                response = await client.post(endpoint, json=sample_data, timeout=timeout, headers=headers)
                logger.info(f"Azure ML health check response code: {response.status_code}")
                # For Azure ML, a 400 (Bad Request) on empty data can still mean the service is up.
                # A 5xx error indicates a server-side problem.
                if response.status_code < 500:
                    ai_model_status = "online"
            else:
                # Local vLLM should respond to a simple GET or HEAD request at its root or a specific health endpoint.
                # Here we check the main endpoint. A 200 is a clear sign of being online.
                response = await client.get(endpoint, timeout=timeout)
                logger.info(f"vLLM health check response code: {response.status_code}")
                if response.status_code == 200:
                    ai_model_status = "online"

    except httpx.TimeoutException:
        logger.warning(f"Health check timed out after {timeout} seconds for {endpoint}")
    except httpx.RequestError as e:
        logger.error(f"Health check failed for {endpoint}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during health check: {e}")

    return {
        "backend_status": "online",
        "ai_model_status": ai_model_status,
        "health_check_interval_seconds": cfg.ai_model.health_check_interval_seconds
    } 