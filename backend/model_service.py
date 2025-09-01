"""
Model Service - Separate FastAPI service for VLLM model management
Runs on port 8001, handles model loading/swapping and inference
"""
import json
import os
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image
import base64
from io import BytesIO

from vllm import LLM, SamplingParams
from vllm.sampling_params import GuidedDecodingParams
from omegaconf import DictConfig, OmegaConf
from pathlib import Path
import sys

# Add backend to path to import modules
sys.path.append(str(Path(__file__).parent))
from app.config import get_config
from app.logger import setup_logging, logger
from app.schemas import LLMResponse
from app.model_utils import generate_llm_prompt


class InferenceRequest(BaseModel):
    images_b64: List[str]  # Base64 encoded images
    job_description: str
    model_config_override: Optional[Dict[str, Any]] = None  # Fixed: renamed from model_config


class ModelSwapRequest(BaseModel):
    model_name: str
    inference_mode: str = "one_shot"  # "one_shot" or "hybrid"


class ModelStatus(BaseModel):
    current_model: Optional[str] = None
    inference_mode: str = "one_shot"
    status: str = "idle"  # "idle", "loading", "swapping", "error"
    gpu_memory_used: Optional[float] = None


class ModelManager:
    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self.vllm_model = None
        self.current_model_name = None
        self.inference_mode = "one_shot"
        self.status = "idle"
        self.is_swapping = False
    
    async def initialize_default_model(self):
        """Initialize the default model from config"""
        try:
            default_model = self.cfg.default_model
            await self.load_model(default_model)
            logger.info(f"Default model {default_model} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize default model: {e}")
            self.status = "error"
    
    async def load_model(self, model_name: str):
        """Load a specific model"""
        self.status = "loading"
        self.is_swapping = True
        
        try:
            # Set environment variables
            if hasattr(self.cfg, 'env_vars'):
                for key, value in self.cfg.env_vars.items():
                    os.environ[str(key)] = str(value)
            
            # Find model in the new config structure
            model_config = None
            
            # Check one_shot models
            if model_name in self.cfg.models.one_shot:
                model_config = self.cfg.models.one_shot[model_name]
            # Check hybrid parser models
            elif model_name in self.cfg.models.hybrid_parser:
                model_config = self.cfg.models.hybrid_parser[model_name]
            # Check hybrid reasoning models
            elif model_name in self.cfg.models.hybrid:
                model_config = self.cfg.models.hybrid[model_name]
            
            if model_config is None:
                raise ValueError(f"Model '{model_name}' not found in configuration")
            
            # Cleanup old model
            if self.vllm_model:
                logger.info("Cleaning up previous model...")
                del self.vllm_model
                # Note: torch.cuda.empty_cache() would go here if we import torch
            
            # Prepare model config
            model_config = OmegaConf.merge(self.cfg.vllm_common_inference_args, model_config)
            
            vllm_config = {
                "model": model_name,
                "gpu_memory_utilization": model_config.gpu_memory_utilization,
                "max_model_len": model_config.max_model_len,
                "enforce_eager": model_config.enforce_eager,
                "tensor_parallel_size": model_config.tensor_parallel_size,
                "trust_remote_code": model_config.trust_remote_code,
                "disable_custom_all_reduce": True,
                "max_num_seqs": model_config.get("max_num_seqs", 4),
                "limit_mm_per_prompt": {"image": self.cfg.app.max_page_size},
            }
            
            logger.info(f"Loading model {model_name} with config: {vllm_config}")
            self.vllm_model = LLM(**vllm_config)
            self.current_model_name = model_name
            self.status = "idle"
            
            logger.info(f"Model {model_name} loaded successfully!")
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            self.status = "error"
            raise e
        finally:
            self.is_swapping = False
    
    async def inference(self, images: List[Image.Image], job_description: str) -> LLMResponse:
        """Perform inference using the loaded model"""
        if not self.vllm_model:
            raise HTTPException(status_code=503, detail="No model loaded")
        
        if self.is_swapping:
            raise HTTPException(status_code=503, detail="Model is swapping, please try again later")
        
        try:
            # Get model config for sampling params
            current_model_config = None
            
            # Find current model in the new config structure
            if self.current_model_name in self.cfg.models.one_shot:
                current_model_config = self.cfg.models.one_shot[self.current_model_name]
            elif self.current_model_name in self.cfg.models.hybrid_parser:
                current_model_config = self.cfg.models.hybrid_parser[self.current_model_name]
            elif self.current_model_name in self.cfg.models.hybrid:
                current_model_config = self.cfg.models.hybrid[self.current_model_name]
            
            if current_model_config is None:
                raise ValueError(f"Current model '{self.current_model_name}' not found in configuration")
            
            model_config = OmegaConf.merge(self.cfg.vllm_common_inference_args, current_model_config)
            
            model_max_len = self.vllm_model.llm_engine.model_config.max_model_len
            max_response_tokens = min(1500, max(512, model_max_len - 500))
            
            # Enforce structured outputs
            guided_decoding_params = GuidedDecodingParams(json=LLMResponse.model_json_schema())
            sampling_params = SamplingParams(
                temperature=model_config.temperature,
                max_tokens=max_response_tokens,
                repetition_penalty=model_config.repetition_penalty,
                guided_decoding=guided_decoding_params,
            )
            
            logger.info(f"Generating response with {len(images)} images and max_tokens={max_response_tokens}")
            multimodal_input = generate_llm_prompt(images, job_description)
            
            outputs = self.vllm_model.generate([multimodal_input], sampling_params)
            llm_content = outputs[0].outputs[0].text.strip()
            parsed_content = json.loads(llm_content)
            validated_response = LLMResponse.model_validate(parsed_content)
            return validated_response
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from vLLM response: {e}")
            if 'llm_content' in locals():
                logger.error(f"Raw response: {llm_content[:500]}...")
            return LLMResponse(outcome="Failed", reason="Error parsing AI response.")
        except Exception as e:
            logger.error(f"An unexpected error occurred during vLLM inference: {e}", exc_info=True)
            return LLMResponse(outcome="Failed", reason="An unexpected error occurred during analysis.")
    
    def get_status(self) -> ModelStatus:
        """Get current model status"""
        return ModelStatus(
            current_model=self.current_model_name,
            inference_mode=self.inference_mode,
            status=self.status
        )


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
    
    # Shutdown
    if model_manager and model_manager.vllm_model:
        del model_manager.vllm_model


app = FastAPI(
    title="Model Service",
    description="VLLM Model Management Service",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
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
        # Start swapping in background
        asyncio.create_task(model_manager.load_model(request.model_name))
        
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
        if  model_config.get("enabled", False):
            one_shot_models[model_name] = {
                "name": model_name,
                "display_name": model_config.get("display_name", model_name),
                "type": model_config.get("type", "multimodal"),
                "max_model_len": model_config.get("max_model_len", 32768)
            }

    # Get hybrid parser (vision model)
    hybrid_parser_models = {}
    for model_name, model_config in cfg.models.hybrid_parser.items():
        if model_config.get("enabled", False):
            hybrid_parser_models[model_name] = {
                "name": model_name,
                "display_name": model_config.get("display_name", model_name),
                "type": model_config.get("type", "vision_ocr"),
                "max_model_len": model_config.get("max_model_len", 8192)
            }

    # Get hybrid reasoning models
    hybrid_reasoning_models = {}
    for model_name, model_config in cfg.models.hybrid.items():
        if model_config.get("enabled", False):
            hybrid_reasoning_models[model_name] = {
                "name": model_name,
                "display_name": model_config.get("display_name", model_name),
                "type": model_config.get("type", "text_reasoning"),
                "max_model_len": model_config.get("max_model_len", 32768)
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
    print("🚀 Starting Model Service on port 8001...")
    print("📍 This service handles VLLM model loading and inference")
    print("🔄 Hot-swapping capabilities enabled")
    print("=" * 50)
    
    uvicorn.run(
        "model_service:app",
        host="0.0.0.0",
        port=8001,
        reload=False,  # Disable reload for model service to avoid reloading large models
        log_level="info"
    )


if __name__ == "__main__":
    main()
