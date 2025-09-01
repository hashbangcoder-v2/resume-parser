import json
import base64
from io import BytesIO
from typing import List
from PIL import Image
import httpx
from omegaconf import DictConfig
from app.logger import logger
from app.schemas import LLMResponse

MODEL_SERVICE_URL = "http://localhost:8001"


def _encode_images_to_base64(images: List[Image.Image]) -> List[str]:
    """Convert PIL Images to base64 strings"""
    encoded_images = []
    for img in images:
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        encoded_images.append(img_str)
    return encoded_images


async def get_model_response(
    cfg: DictConfig, 
    images: List[Image.Image], 
    job_description: str, 
) -> LLMResponse:    
    """
    Get model response from the model service.
    This replaces the direct VLLM inference and maintains backward compatibility.
    """
    if cfg.app.env == "prod":
        return await query_azure_ml_endpoint() 
    else:
        return await query_model_service(images, job_description)


async def query_model_service(
    images: List[Image.Image], 
    job_description: str,     
) -> LLMResponse:
    """
    Performs inference via the model service (replaces query_vllm).
    """
    try:
        # Encode images to base64
        images_b64 = _encode_images_to_base64(images)
        
        # Prepare request payload
        request_data = {
            "images_b64": images_b64,
            "job_description": job_description
        }
        
        logger.info(f"Sending inference request with {len(images)} images to model service")
        
        # Call model service
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5-minute timeout for inference
            response = await client.post(
                f"{MODEL_SERVICE_URL}/inference",
                json=request_data
            )
            
            if response.status_code == 200:
                result_data = response.json()
                logger.info(f"Model service returned result: {result_data.get('outcome', 'Unknown')}")
                return LLMResponse(**result_data)
            elif response.status_code == 503:
                logger.warning("Model service unavailable (swapping?)")
                return LLMResponse(
                    outcome="Failed", 
                    reason="Model service temporarily unavailable (may be swapping models)"
                )
            else:
                logger.error(f"Model service error: {response.status_code} - {response.text}")
                return LLMResponse(
                    outcome="Failed", 
                    reason=f"Model service error: {response.status_code}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to model service: {e}")
        return LLMResponse(
            outcome="Failed", 
            reason="Failed to connect to model service"
        )
    except Exception as e:
        logger.error(f"Unexpected error in model service communication: {e}")
        return LLMResponse(
            outcome="Failed", 
            reason="Unexpected error during model inference"
        )


async def check_model_service_health() -> bool:
    """Check if model service is healthy"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{MODEL_SERVICE_URL}/health")
            return response.status_code == 200
    except:
        return False


async def query_azure_ml_endpoint() -> LLMResponse:
    """
    Queries the Azure ML Online Endpoint.
    """
    raise NotImplementedError("Azure ML Online Endpoint is not implemented yet.")