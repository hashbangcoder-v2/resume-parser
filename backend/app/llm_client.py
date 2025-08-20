import httpx
import json
import dotenv
from omegaconf import DictConfig
from typing import List, Optional
from PIL import Image
from app.logger import logger
from app.schemas import LLMResponse
from app.common_utils import get_system_prompt, image_to_base64
from vllm import LLM, SamplingParams
from app.craft_prompt import generate_llm_prompt


vllm_model = None

def initialize_vllm(cfg: DictConfig):
    """
    Initializes and loads the vLLM model based on the configuration.
    """
    global vllm_model
        
    logger.info("🔧 Setting vLLM environment variables from config:")
    import os
    if hasattr(cfg.vllm, 'env_vars'):
        for key, value in cfg.vllm.env_vars.items():
            os.environ[str(key)] = str(value)
            logger.info(f"  {key}={value}")
    
    model_name = cfg.ai_model.default
    supported_models = cfg.ai_model.models
    if model_name not in supported_models:
        logger.error(f"vLLM model '{model_name}' is not supported. Please check the supported models in dev.yaml.")
        return    
    
    try:
        logger.info(f"🚀 Loading vLLM model: {model_name}")                
        vllm_inference_args = cfg.vllm.inference_args
        
        vllm_config = {
            "model": model_name,
            "gpu_memory_utilization": vllm_inference_args.gpu_memory_utilization,
            "max_model_len": vllm_inference_args.max_model_len,
            "enforce_eager": vllm_inference_args.enforce_eager,
            "tensor_parallel_size": vllm_inference_args.tensor_parallel_size,
            "trust_remote_code": vllm_inference_args.trust_remote_code,
            "disable_custom_all_reduce": True,  
            "max_num_seqs": vllm_inference_args.get("max_num_seqs", 4),     
            "block_size": 16,  
            "limit_mm_per_prompt": vllm_inference_args.get("limit_mm_per_prompt", {"image": 3}),  
        }
        
        logger.info("⚙️  vLLM Configuration:")
        for key, value in vllm_config.items():
            logger.info(f"  {key}: {value}")
            
        vllm_model = LLM(**vllm_config)
        logger.info("✅ vLLM model loaded successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to load vLLM model: {e}")
        raise e



async def get_model_response(
    cfg: DictConfig, 
    images: List[Image.Image], 
    job_description: str, 
) -> LLMResponse:    
    if cfg.app.env == "prod":
        return await query_azure_ml_endpoint() 
    else:
        return await query_vllm(cfg, images, job_description)



async def query_vllm(
    cfg: DictConfig, 
    images: List[Image.Image], 
    job_description: str,     
) -> LLMResponse:
    """
    Performs offline inference using the pre-loaded vLLM model.
    """
    if not vllm_model:
        logger.error("vLLM model is not available for inference.")
        return LLMResponse(outcome="Failed", reason="vLLM model not loaded.")
    
    try:                
        model_max_len = vllm_model.llm_engine.model_config.max_model_len
        max_response_tokens = min(1500, max(512, model_max_len - 500))
        
        sampling_params = SamplingParams(
            temperature=cfg.vllm.inference_args.temperature,
            max_tokens=max_response_tokens,            
            repetition_penalty=cfg.vllm.inference_args.repetition_penalty,
        )

        logger.info(f"Generating response with {len(images)} images and max_tokens={max_response_tokens}")
        multimodal_input = generate_llm_prompt(images, job_description)

        outputs = vllm_model.generate([multimodal_input], sampling_params)
        llm_content = outputs[0].outputs[0].text
        
        parsed_content = json.loads(llm_content)
        validated_response = LLMResponse.model_validate(parsed_content)
        return validated_response

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON from vLLM response: {e}")
        logger.error(f"Raw response: {llm_content[:500]}...")
        return LLMResponse(outcome="Failed", reason="Error parsing AI response.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during vLLM inference: {e}", exc_info=True)
        return LLMResponse(outcome="Failed", reason="An unexpected error occurred during analysis.")



async def query_azure_ml_endpoint() -> LLMResponse:
    """
    Queries the Azure ML Online Endpoint.
    """
    raise NotImplementedError("Azure ML Online Endpoint is not implemented yet.")
