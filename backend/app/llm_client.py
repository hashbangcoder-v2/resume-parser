import httpx
import json
from omegaconf import DictConfig
from typing import List, Optional
from PIL import Image
import logging
from app.schemas import LLMResponse
from app.common_utils import get_system_prompt, image_to_base64

# Conditional imports for vLLM
try:
    from vllm import LLM, SamplingParams
    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False

logger = logging.getLogger(__name__)

# Global variable to hold the loaded vLLM model
vllm_model = None

def initialize_vllm(cfg: DictConfig):
    """
    Initializes and loads the vLLM model based on the configuration.
    """
    global vllm_model
    if not VLLM_AVAILABLE:
        logger.warning("vLLM is not installed. Local inference will not be available.")
        return

    model_name = cfg.ai_model.default
    supported_models = cfg.ai_model.models
    if model_name not in supported_models:
        logger.error(f"vLLM model '{model_name}' is not supported. Please check the supported models in dev.yaml.")
        return    
    
    try:
        logger.info(f"Loading vLLM model: {model_name}")
        # Try loading with AWQ quantization first
        try:
            vllm_model = LLM(
                model=model_name,
                quantization="awq",  # Use AWQ quantization to reduce memory usage
                gpu_memory_utilization=0.85,  # Use 85% of GPU memory, leave buffer for other processes
                max_model_len=4096,  # Reduce max sequence length to save memory
                enforce_eager=True,  # Use eager execution to reduce memory fragmentation
                tensor_parallel_size=1,  # Single GPU setup
            )
            logger.info("vLLM model loaded successfully with AWQ quantization.")
        except Exception as awq_error:
            logger.warning(f"AWQ quantization failed: {awq_error}. Trying with standard settings...")
            # Fallback to standard loading with conservative memory settings
            vllm_model = LLM(
                model=model_name,
                gpu_memory_utilization=0.75,  # Use even less GPU memory
                max_model_len=2048,  # Further reduce max sequence length
                enforce_eager=True,  # Use eager execution to reduce memory fragmentation
                tensor_parallel_size=1,  # Single GPU setup
            )
            logger.info("vLLM model loaded successfully with conservative settings.")
    except Exception as e:
        logger.error(f"Failed to load vLLM model with all attempted configurations: {e}")
        logger.error("Suggestions:")
        logger.error("1. Try using a smaller model or quantized version")
        logger.error("2. Ensure no other processes are using GPU memory")
        logger.error("3. Set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True")
        vllm_model = None

async def get_model_response(
    cfg: DictConfig, 
    images: List[Image.Image], 
    job_description: str, 
    model_name: Optional[str] = None
) -> LLMResponse:
    if model_name is None:
        model_name = cfg.ai_model.default

    if cfg.app.env == "prod":
        return await query_azure_ml_endpoint(cfg, images, job_description, model_name)
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
        
        sampling_params = SamplingParams(
            temperature=cfg.ai_model.temperature,
            max_tokens=1500,
        )

        outputs = await vllm_model.generate(prompt, sampling_params)
        
        # Assuming the first output is the one we want
        llm_content = outputs[0].outputs[0].text
        parsed_content = json.loads(llm_content)
        
        validated_response = LLMResponse.model_validate(parsed_content)
        return validated_response

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON from vLLM response: {e}")
        return LLMResponse(outcome="Failed", reason="Error parsing AI response.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during vLLM inference: {e}")
        return LLMResponse(outcome="Failed", reason="An unexpected error occurred during analysis.")

async def query_azure_ml_endpoint(
    cfg: DictConfig, 
    images: List[Image.Image], 
    job_description: str,
    model_name: str
) -> LLMResponse:
    """
    Queries the Azure ML Online Endpoint.
    """
    model_config = cfg.ai_model.models.get(model_name)
    if not model_config or not hasattr(model_config, 'api_key') or not hasattr(model_config, 'endpoint'):
        logger.error(f"Configuration for Azure ML model '{model_name}' is incomplete.")
        return LLMResponse(outcome="Failed", reason=f"Configuration for model '{model_name}' is incomplete.")

    base64_images = [image_to_base64(img) for img in images]
    system_prompt = get_system_prompt()
    
    user_prompt = f"""
    Here is the job description:
    ---
    {job_description}
    ---
    Analyze the attached resume and provide your assessment in a JSON object with 'outcome' and 'reason'.
    """

    payload = {
        "input_data": {
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        *[{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}} for img_b64 in base64_images]
                    ]
                }
            ],
            "temperature": cfg.ai_model.temperature,
            "max_tokens": 1500,
        }
    }

    headers = {
        'Authorization': f'Bearer {model_config.api_key}',
        'Content-Type': 'application/json'
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(model_config.endpoint, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            raw_response = response.json()
            if isinstance(raw_response, str):
                llm_content = json.loads(raw_response)
            else:
                llm_content = raw_response

            if isinstance(llm_content, list):
                parsed_content = json.loads(llm_content[0])
            else:
                parsed_content = llm_content
                
            validated_response = LLMResponse.model_validate(parsed_content)
            return validated_response
            
        except (httpx.RequestError, httpx.TimeoutException, json.JSONDecodeError) as e:
            logger.error(f"Error querying or parsing Azure ML endpoint response: {e}")
            return LLMResponse(outcome="Failed", reason="Error during AI analysis.")
        except Exception as e:
            logger.error(f"An unexpected error occurred in Azure ML query: {e}")
            return LLMResponse(outcome="Failed", reason="An unexpected error occurred during analysis.")
