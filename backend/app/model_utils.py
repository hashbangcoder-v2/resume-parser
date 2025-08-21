# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from typing import List
from PIL import Image

from app.common_utils import get_system_prompt


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


