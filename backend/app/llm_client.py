import base64
import httpx
from omegaconf import DictConfig
from typing import List
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

def image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

async def get_model_response(cfg: DictConfig, images: List[Image.Image]) -> dict:
    if cfg.APP_ENV == "prod":
        return await _query_azure_ml_endpoint(cfg, images)
    else:
        return await _query_vllm_endpoint(cfg, images)

async def _query_vllm_endpoint(cfg: DictConfig, images: List[Image.Image]) -> dict:
    """
    Queries the local vLLM OpenAI-compatible server.
    This assumes a multi-modal model like Qwen-VL or LLaVA.
    """
    base64_images = [image_to_base64(img) for img in images]
    
    payload = {
        "model": "qwen:7b", # This is often ignored but good practice
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this resume and provide a summary. Extract the candidate's name, skills, and experience. Determine if they are a good fit for a software engineering role."},
                    *[{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}} for img_b64 in base64_images]
                ]
            }
        ],
        "max_tokens": 1500,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(cfg.ai_model.endpoint, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.error(f"Error querying vLLM endpoint: {e}")
            return {"error": str(e)}

async def _query_azure_ml_endpoint(cfg: DictConfig, images: List[Image.Image]) -> dict:
    """
    Queries the Azure ML Online Endpoint.
    The data format must match what the scoring script of your deployed model expects.
    """
    base64_images = [image_to_base64(img) for img in images]

    # This is a common format for Azure ML endpoints, but you may need to adjust it.
    payload = {
        "input_data": {
            "columns": ["prompt", "images"],
            "data": [
                ["Analyze this resume and provide a summary...", base64_images]
            ]
        }
    }

    headers = {
        'Authorization': f'Bearer {cfg.azure_ml.api_key}', # Assuming API key auth
        'Content-Type': 'application/json'
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(cfg.ai_model.endpoint, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.error(f"Error querying Azure ML endpoint: {e}")
            return {"error": str(e)} 