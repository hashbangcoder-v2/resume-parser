"""
Model Management Router - Handles model selection and hot-swapping
Communicates with the separate model service
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel
import httpx
from app.db import get_db
from app.logger import logger

router = APIRouter(
    prefix="/api/models",
    tags=["models"],
)

MODEL_SERVICE_URL = "http://localhost:8001"


class ModelSwapRequest(BaseModel):
    model_name: str
    inference_mode: str = "one_shot"


@router.get("/available")
async def get_available_models():
    """Get available models and inference modes from model service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MODEL_SERVICE_URL}/models/available")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=503, detail="Model service unavailable")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Model service connection failed")


@router.get("/status")
async def get_model_status():
    """Get current model status from model service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MODEL_SERVICE_URL}/status")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=503, detail="Model service unavailable")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Model service connection failed")


@router.post("/swap")
async def swap_model(request: ModelSwapRequest):
    """Trigger model hot-swap via model service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MODEL_SERVICE_URL}/swap",
                json=request.dict()
            )
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Model swap initiated: {request.model_name}")
                return data
            else:
                error_detail = response.json().get("detail", "Unknown error")
                raise HTTPException(status_code=response.status_code, detail=error_detail)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Model service connection failed")


@router.get("/health")
async def check_model_service_health():
    """Check if model service is healthy"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MODEL_SERVICE_URL}/health")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=503, detail="Model service unhealthy")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Model service connection failed")
