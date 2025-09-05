# Handles VLLM model lifecycle, loading, and inference

import os
import json
import gc
import torch
from typing import List, Optional
from PIL import Image
from fastapi import HTTPException
from vllm import LLM, SamplingParams
from vllm.sampling_params import GuidedDecodingParams
from omegaconf import DictConfig, OmegaConf

from app.logger import logger
from app.schemas import LLMResponse
from .utils import generate_llm_prompt, get_model_handler


class ModelStatus:
    """Model status data class"""
    def __init__(self, current_model: Optional[str] = None, inference_mode: str = "one_shot", 
                 status: str = "idle"):
        self.current_model = current_model
        self.inference_mode = inference_mode
        self.status = status        
    
    def dict(self):
        return {
            "current_model": self.current_model,
            "inference_mode": self.inference_mode,
            "status": self.status,            
        }


class ModelManager:
    """Manages VLLM model lifecycle and inference"""
    
    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self.vllm_model = None
        self.current_model_name = None
        self.inference_mode = "one_shot"
        self.status = "idle"
        self.is_swapping = False
    
    def _get_model_config(self, model_name: str) -> DictConfig:
        """
        Get model configuration by name from any category.
        
        Args:
            model_name: Name of the model to find
            
        Returns:
            DictConfig: Model configuration
            
        Raises:
            ValueError: If model not found in any category
        """
        # Define search order and corresponding config paths
        config_sources = [
            ('one_shot', self.cfg.models.one_shot),
            ('hybrid_parser', self.cfg.models.hybrid_parser), 
            ('hybrid', self.cfg.models.hybrid)
        ]
        
        for category, config_dict in config_sources:
            if model_name in config_dict:
                logger.debug(f"Found model '{model_name}' in category '{category}'")
                return config_dict[model_name]
        
        # Model not found in any category
        available_models = []
        for category, config_dict in config_sources:
            available_models.extend(f"{category}:{name}" for name in config_dict.keys())
        
        raise ValueError(
            f"Model '{model_name}' not found in configuration. "
            f"Available models: {', '.join(available_models)}"
        )
    
    @property
    def available_models(self) -> dict:
        """
        Get all available models organized by category.
        
        Returns:
            dict: Dictionary with categories as keys and model lists as values
        """
        return {
            'one_shot': list(self.cfg.models.one_shot.keys()),
            'hybrid_parser': list(self.cfg.models.hybrid_parser.keys()),
            'hybrid': list(self.cfg.models.hybrid.keys())
        }

    def _cleanup_gpu_memory(self):
        """Comprehensive GPU memory cleanup"""
        logger.info("Starting GPU memory cleanup...")
        
        try:
            # Step 1: Delete the VLLM model
            if hasattr(self, 'vllm_model') and self.vllm_model is not None:
                logger.info("Deleting VLLM model...")
                del self.vllm_model
                self.vllm_model = None
            
            # Step 2: Force Python garbage collection
            logger.info("Running garbage collection...")
            gc.collect()
            
            logger.info("Clearing CUDA cache...")
            # Clear PyTorch CUDA cache
            torch.cuda.empty_cache()
            
            # Force synchronization
            torch.cuda.synchronize()
            
            # Get memory info for logging
            try:
                memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
                memory_cached = torch.cuda.memory_reserved() / 1024**3     # GB
                logger.info(f"GPU Memory after cleanup - Allocated: {memory_allocated:.2f}GB, Cached: {memory_cached:.2f}GB")
            except Exception as mem_error:
                logger.warning(f"Could not get GPU memory info: {mem_error}")
            logger.info("GPU memory cleanup completed")
            
        except Exception as cleanup_error:
            logger.error(f"Error during GPU memory cleanup: {cleanup_error}")
            # Don't raise the error, as this is cleanup - continue with model loading
    
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
            # Set env variables
            if hasattr(self.cfg, 'env_vars'):
                for key, value in self.cfg.env_vars.items():
                    os.environ[str(key)] = str(value)
            
            # Get model configuration using the clean lookup method
            model_config = self._get_model_config(model_name)
            
            # Cleanup old model with comprehensive GPU memory cleanup
            if hasattr(self, 'vllm_model') and self.vllm_model is not None:
                logger.info("Cleaning up previous model...")
                self._cleanup_gpu_memory()                
            
            # Merge with common configuration
            merged_config = OmegaConf.merge(self.cfg.vllm_common_inference_args, model_config)
            
            # Get model-specific handler and configuration
            handler = get_model_handler(model_name, merged_config, self.cfg.vllm_common_inference_args)
            vllm_config = handler.get_vllm_config()
            
            # Remove None values to avoid VLLM errors
            vllm_config = {k: v for k, v in vllm_config.items() if v is not None}
            
            handler_info = handler.get_handler_info()
            logger.info(f"Loading {handler_info['model_family']} model {model_name} using {handler_info['handler_class']}")
            logger.info(f"VLLM config: {vllm_config}")
            self.vllm_model = LLM(**vllm_config)
            self.current_model_name = model_name
            self.status = "idle"
            
            logger.info(f"Model {model_name} loaded successfully!")
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            self.status = "error"
            
            # Ensure vllm_model attribute exists even on error
            if not hasattr(self, 'vllm_model'):
                self.vllm_model = None
                
            # Try to reset to a known state
            self.current_model_name = None
            raise e
        finally:
            self.is_swapping = False
    
    async def recover_model(self):
        """Attempt to recover by loading the default model"""
        try:
            logger.info("Attempting model recovery...")
            
            # Force cleanup before recovery attempt
            logger.info("Performing cleanup before recovery...")
            self._cleanup_gpu_memory()
            
            # fall back to default model
            default_model = self.cfg.default_model
            if default_model != self.current_model_name:
                logger.info(f"Attempting to reload default model: {default_model}")
                await self.load_model(default_model)
                return
            else:
                logger.warning(f"Current model is already the default model: {default_model}")
                # Try to restart the default model anyway
                logger.info("Restarting default model...")
                await self.load_model(default_model)
                
        except Exception as e:
            logger.error(f"Model recovery failed: {e}")
            self.status = "error"
    
    async def inference(self, images: List[Image.Image], job_description: str) -> LLMResponse:
        """Perform inference using the loaded model"""
        if not self.vllm_model:
            raise HTTPException(status_code=503, detail="No model loaded")
        
        if self.is_swapping:
            raise HTTPException(status_code=503, detail="Model is swapping, please try again later")
        
        try:
            # Get model config for sampling params using the clean lookup method
            current_model_config = self._get_model_config(self.current_model_name)
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
