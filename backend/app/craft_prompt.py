# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from typing import List
from PIL import Image

from app.common_utils import get_system_prompt



def generate_llm_prompt(images: List[Image.Image], job_description: str) -> dict:
    system_prompt = get_system_prompt()
    question = f"Here is the job description: {job_description}"
    prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"        
        "<|vision_bos|><|IMAGE|><|vision_eos|>"        
        f"{question}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    
    model_inputs={
            "prompt": prompt,
            "multi_modal_data": {                
                "image": images,                
            },
        }
    
    return model_inputs


