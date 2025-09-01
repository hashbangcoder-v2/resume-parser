from vllm import LLM, SamplingParams
from pdf2image import convert_from_path
from pathlib import Path
from app.model_utils import get_system_prompt
from omegaconf import OmegaConf
from vllm.sampling_params import GuidedDecodingParams
from app.schemas import LLMResponse

vllm_model = None


model_name = "Qwen/Qwen2.5-Omni-7B"

vllm_inference_args = OmegaConf.create({
    "gpu_memory_utilization": 0.65,
    "max_model_len": 32768,
    "enforce_eager": True,
    "tensor_parallel_size": 1,
    "trust_remote_code": True,
})

vllm_config = {
    "model": model_name,
    "gpu_memory_utilization": vllm_inference_args.gpu_memory_utilization,
    "max_model_len": vllm_inference_args.max_model_len,
    "enforce_eager": vllm_inference_args.enforce_eager,
    "tensor_parallel_size": vllm_inference_args.tensor_parallel_size,
    "trust_remote_code": vllm_inference_args.trust_remote_code,
    "disable_custom_all_reduce": True,  # Stability improvement
    "max_num_seqs": vllm_inference_args.get("max_num_seqs", 4),  # Use config value for multimodal
    "block_size": 16,  # Memory block size
    "limit_mm_per_prompt": vllm_inference_args.get("limit_mm_per_prompt", {"image": 3}),  # Multimodal limits
}

vllm_model = LLM(**vllm_config)
pdf_file = Path('/home/azureuser/localfiles/resume-parser/sample.pdf')

images = convert_from_path(pdf_file)
guided_decoding_params = GuidedDecodingParams(    
    json=LLMResponse.model_json_schema(),
)
system_prompt = get_system_prompt()
question = "Analyze the attached resume images above and provide your assessment."
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

sampling_params = SamplingParams(temperature=0.7, max_tokens=1024, guided_decoding=guided_decoding_params)


outputs = vllm_model.generate(model_inputs, sampling_params=sampling_params)

for o in outputs:
    generated_text = o.outputs[0].text
    print(generated_text)



