# Handles VLLM model lifecycle, loading, and inference

import os
import json
from typing import List, Optional
from PIL import Image
from fastapi import HTTPException
from vllm import LLM, SamplingParams
from vllm.sampling_params import GuidedDecodingParams
from omegaconf import DictConfig, OmegaConf

from app.logger import logger
from app.schemas import LLMResponse
from app.model_utils import generate_llm_prompt, get_model_handler


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
            
            # Cleanup old model - with defensive check
            if hasattr(self, 'vllm_model') and self.vllm_model is not None:
                logger.info("Cleaning up previous model...")
                try:
                    del self.vllm_model
                except Exception as cleanup_error:
                    logger.warning(f"Error during model cleanup: {cleanup_error}")
                finally:
                    self.vllm_model = None                
            
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
            
            # Always fall back to default model
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
