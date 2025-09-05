
# Model Service - FastAPI service for VLLM model management handles model loading/swapping and inference

import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image
import base64
from io import BytesIO

from app.config import get_config
from app.logger import setup_logging, logger
from app.models import ModelManager


class InferenceRequest(BaseModel):
    images_b64: List[str]  
    job_description: str
    model_config_override: Optional[dict] = None  


class ModelSwapRequest(BaseModel):
    model_name: str
    inference_mode: str = "one_shot"  # "one_shot" or "hybrid"


# Global model manager
model_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for model service startup and shutdown"""
    global model_manager
    
    # Startup
    cfg = get_config()
    setup_logging(cfg)
    model_manager = ModelManager(cfg)
    
    # Load default model
    await model_manager.initialize_default_model()
    
    yield
    
    # Shutdown - comprehensive cleanup
    if model_manager:
        logger.info("Shutting down model service...")
        model_manager._cleanup_gpu_memory()
        logger.info("Model service shutdown completed")


app = FastAPI(
    title="Model Service",
    description="VLLM Model Management Service",    
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    
    status = model_manager.get_status()
    return {
        "status": "healthy" if status.status != "error" else "unhealthy",
        "model_status": status.dict()
    }


@app.get("/status")
async def get_status():
    """Get current model status"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    
    return model_manager.get_status().dict()


@app.post("/swap")
async def swap_model(request: ModelSwapRequest):
    """Swap to a different model"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    
    try:
        # Start swapping in background with error handling
        async def swap_with_recovery():
            try:
                await model_manager.load_model(request.model_name)
                logger.info(f"Model swap to {request.model_name} completed successfully")
            except Exception as swap_error:
                logger.error(f"Model swap to {request.model_name} failed: {swap_error}")
                # Attempt recovery with default
                await model_manager.recover_model()
        
        asyncio.create_task(swap_with_recovery())
        
        return {
            "status": "swapping",
            "target_model": request.model_name,
            "inference_mode": request.inference_mode,
            "eta_seconds": 45
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start model swap: {str(e)}")


@app.post("/inference")
async def inference(request: InferenceRequest):
    """Perform inference with the current model"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    
    try:
        # Decode base64 images
        images = []
        for img_b64 in request.images_b64:
            img_data = base64.b64decode(img_b64)
            img = Image.open(BytesIO(img_data))
            images.append(img)
        
        # Perform inference
        result = await model_manager.inference(images, request.job_description)
        return result.dict()
        
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.get("/models/available")
async def get_available_models():
    """Get list of available models"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    
    cfg = model_manager.cfg
    
    # Get one-shot models directly from config
    one_shot_models = {}
    for model_name, model_config in cfg.models.one_shot.items():
        if model_config.get("enabled", False):
            one_shot_models[model_name] = {
                "name": model_name,
                "display_name": model_config.get("display_name", model_name),
                "type": model_config.get("type", "multimodal"),
                "max_model_len": model_config.get("max_model_len")
            }

    # Get oCr parser (vision model)
    hybrid_parser_models = {}
    for model_name, model_config in cfg.models.hybrid_parser.items():
        if model_config.get("enabled", False):
            hybrid_parser_models[model_name] = {
                "name": model_name,
                "display_name": model_config.get("display_name", model_name),
                "type": model_config.get("type", "vision_ocr"),
                "max_model_len": model_config.get("max_model_len")
            }

    # Get hybrid reasoning models
    hybrid_reasoning_models = {}
    for model_name, model_config in cfg.models.hybrid.items():
        if model_config.get("enabled", False):
            hybrid_reasoning_models[model_name] = {
                "name": model_name,
                "display_name": model_config.get("display_name", model_name),
                "type": model_config.get("type", "text_reasoning"),
                "max_model_len": model_config.get("max_model_len")
            }

    # Create hybrid combinations by pairing each parser with each reasoning model
    hybrid_model_combinations = {}
    for parser_name, parser_config in hybrid_parser_models.items():
        for reasoning_name, reasoning_config in hybrid_reasoning_models.items():
            combo_name = f"{parser_config['display_name']} + {reasoning_config['display_name']}"
            hybrid_model_combinations[combo_name] = {
                "name": combo_name,
                "display_name": combo_name,
                "type": "hybrid_combination",                
                "vision_model": parser_name,
                "reasoning_model": reasoning_name
            }

    # Get inference mode configurations
    inference_modes_config = cfg.get("inference_modes", {})
    
    return {
        "inference_modes": {
            "one_shot": {
                "display_name": inference_modes_config.get("one_shot", {}).get("display_name", "One-Shot"),
                "description": inference_modes_config.get("one_shot", {}).get("description", "Single multimodal model processes images directly"),
                "hover_text": inference_modes_config.get("one_shot", {}).get("hover_text", "Single multimodal model that directly processes PDF images"),
                "models": one_shot_models
            },
            "hybrid": {
                "display_name": inference_modes_config.get("hybrid", {}).get("display_name", "Hybrid"),
                "description": inference_modes_config.get("hybrid", {}).get("description", "Two-stage: Vision extraction + Text reasoning"),
                "hover_text": inference_modes_config.get("hybrid", {}).get("hover_text", "Two-stage pipeline using vision and reasoning models"),
                "models": hybrid_model_combinations
            }
        },
        "current_mode": model_manager.inference_mode,
        "current_model": model_manager.current_model_name
    }


def main():
    """Main entry point for wfc-model-serve command"""
    import uvicorn
    print("Starting Model Service on port 8001...")
    print("This service handles VLLM model loading and inference")
    print("Hot-swapping capabilities enabled")
    print("=" * 50)
    
    uvicorn.run(
        "model_service:app",
        host="0.0.0.0",
        port=8001,
        reload=False, 
        log_level="info"
    )


if __name__ == "__main__":
    main()