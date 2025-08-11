import httpx
import json
import dotenv
from omegaconf import DictConfig
from typing import List, Optional
from PIL import Image
from app.logger import logger
from app.schemas import LLMResponse
from app.common_utils import get_system_prompt, image_to_base64

# Conditional imports for vLLM
try:
    from vllm import LLM, SamplingParams
    VLLM_AVAILABLE = True    
except ImportError:
    VLLM_AVAILABLE = False
    raise ImportError("vLLM is not installed. Please install it with `pip install vllm`.")

# Global variable to hold the loaded vLLM model
vllm_model = None

def initialize_vllm(cfg: DictConfig):
    """
    Initializes and loads the vLLM model based on the configuration.
    """
    global vllm_model
        
    # Set environment variables from config BEFORE any vLLM operations
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
    
    # Clear CUDA cache and check memory
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            # Get memory info
            gpu_props = torch.cuda.get_device_properties(0)
            memory_total = gpu_props.total_memory / 1e9
            memory_allocated = torch.cuda.memory_allocated(0) / 1e9
            memory_cached = torch.cuda.memory_reserved(0) / 1e9
            memory_free = memory_total - memory_cached
            
            logger.info(f"🔍 GPU Memory Status:")
            logger.info(f"  Total: {memory_total:.2f} GB")
            logger.info(f"  Allocated: {memory_allocated:.2f} GB")
            logger.info(f"  Cached: {memory_cached:.2f} GB") 
            logger.info(f"  Free: {memory_free:.2f} GB")
                
    except Exception as mem_error:
        logger.warning(f"Could not check GPU memory: {mem_error}")
    
    try:
        logger.info(f"🚀 Loading vLLM model: {model_name}")
        
        # Get vLLM configuration from dev.yaml
        vllm_inference_args = cfg.vllm.inference_args
        
        vllm_config = {
            "model": model_name,
            "quantization": "awq",  # Use standard AWQ, not awq_marlin
            "gpu_memory_utilization": vllm_inference_args.gpu_memory_utilization,
            "max_model_len": vllm_inference_args.max_model_len,
            "enforce_eager": vllm_inference_args.enforce_eager,
            "tensor_parallel_size": vllm_inference_args.tensor_parallel_size,
            "trust_remote_code": vllm_inference_args.trust_remote_code,
            "disable_custom_all_reduce": True,  # Stability improvement
            "max_num_seqs": 32,  # Conservative concurrent sequences
            "block_size": 16,  # Memory block size
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
    model_name: Optional[str] = None
) -> LLMResponse:
    if model_name is None:
        model_name = cfg.ai_model.default

    if cfg.app.env == "prod":
        return await query_azure_ml_endpoint() 
    else:
        return await query_vllm(cfg, images, job_description, model_name)



async def query_vllm(
    cfg: DictConfig, 
    images: List[Image.Image], 
    job_description: str, 
    model_name: str
) -> LLMResponse:
    """
    Performs offline inference using the pre-loaded vLLM model.
    """
    if not vllm_model:
        logger.error("vLLM model is not available for inference.")
        return LLMResponse(outcome="Needs Review", reason="vLLM model not loaded.")

    system_prompt = get_system_prompt()
    user_prompt = f"""
    Here is the job description:
    ---
    {job_description}
    ---
    Analyze the attached resume and provide your assessment.
    """
    
    conversation = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user", 
            "content": [
                {"type": "text", "text": user_prompt},
                *[{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_to_base64(img)}"}} for img in images]
            ]
        }
    ]

    try:
        # vLLM uses a different prompt format; we need to apply the chat template
        prompt = vllm_model.llm_engine.tokenizer.apply_chat_template(
            conversation=conversation, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # Adaptive max_tokens based on model's max_model_len
        model_max_len = getattr(vllm_model.llm_engine.model_config, 'max_model_len', 2048)
        # Reserve space for input prompt (estimate ~500 tokens for resume analysis)
        max_response_tokens = min(1500, max(512, model_max_len - 500))
        
        sampling_params = SamplingParams(
            temperature=cfg.ai_model.temperature,
            max_tokens=max_response_tokens,
            stop=["</s>", "<|endoftext|>"],  # Add proper stop tokens
            repetition_penalty=1.1,  # Prevent repetitive outputs
        )

        logger.info(f"Generating response with max_tokens={max_response_tokens}")
        outputs = vllm_model.generate(prompt, sampling_params)
        
        # Assuming the first output is the one we want
        llm_content = outputs[0].outputs[0].text.strip()
        logger.debug(f"Raw LLM response: {llm_content[:200]}...")
        
        # Try to extract JSON from the response if it's wrapped in text
        if not llm_content.startswith('{'):
            # Look for JSON content within the response
            import re
            json_match = re.search(r'\{.*\}', llm_content, re.DOTALL)
            if json_match:
                llm_content = json_match.group(0)
            else:
                logger.warning("No JSON found in response, attempting to parse as-is")
        
        parsed_content = json.loads(llm_content)
        
        validated_response = LLMResponse.model_validate(parsed_content)
        return validated_response

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON from vLLM response: {e}")
        return LLMResponse(outcome="Failed", reason="Error parsing AI response.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during vLLM inference: {e}")
        return LLMResponse(outcome="Failed", reason="An unexpected error occurred during analysis.")



async def query_azure_ml_endpoint() -> LLMResponse:
    """
    Queries the Azure ML Online Endpoint.
    """
    raise NotImplementedError("Azure ML Online Endpoint is not implemented yet.")
