# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from typing import List
from PIL import Image
from pathlib import Path
from functools import lru_cache
from app.config import get_config

cfg = get_config()

@lru_cache(maxsize=1)
def get_system_prompt() -> str:
    prompt_path = Path(cfg.models.prompt_path)
    with open(prompt_path, "r") as f:
        return f.read()


def generate_llm_prompt(images: List[Image.Image], job_description: str) -> dict:
    """Generate prompt for multimodal inference."""
    system_prompt = get_system_prompt()
    img_token = "<|vision_bos|><|IMAGE|><|vision_eos|>\n" * len(images)
    question = f"Here is the job description: {job_description}\n\nAnalyze the attached resume images and provide your assessment."
    
    prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"        
        f"{img_token}"
        f"<|im_start|>user\n{question}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    
    model_inputs = {
        "prompt": prompt,
        "multi_modal_data": {                
            "image": images,                
        },
    }
    
    return model_inputs


