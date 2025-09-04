#  Model-specific VLLM configuration handlers

from abc import ABC, abstractmethod
from typing import Dict, Any
from omegaconf import DictConfig


class BaseModelHandler(ABC):
    """Abstract base class for model-specific VLLM configurations"""
    
    def __init__(self, model_name: str, model_config: DictConfig, common_config: DictConfig):
        self.model_name = model_name
        self.model_config = model_config
        self.common_config = common_config
    
    @abstractmethod
    def get_vllm_config(self) -> Dict[str, Any]:
        """Return VLLM-specific configuration for this model"""
        pass
    
    def get_handler_info(self) -> Dict[str, str]:
        """Return information about this handler for debugging"""
        return {
            "handler_class": self.__class__.__name__,
            "model_name": self.model_name,
            "model_family": self.get_model_family()
        }
    
    def get_model_family(self) -> str:
        """Return the model family name"""
        return "unknown"
    
    def get_base_config(self) -> Dict[str, Any]:
        """Get base configuration common to all models"""
        return {
            "model": self.model_name,
            "gpu_memory_utilization": self.model_config.gpu_memory_utilization,
            "max_model_len": self.model_config.max_model_len,
            "enforce_eager": self.model_config.enforce_eager,
            "tensor_parallel_size": self.model_config.tensor_parallel_size,
            "trust_remote_code": self.model_config.trust_remote_code,
            "disable_custom_all_reduce": True,
            "max_num_seqs": self.model_config.get("max_num_seqs", 4),
        }


class QwenModelHandler(BaseModelHandler):            
    def get_vllm_config(self) -> Dict[str, Any]:
        config = self.get_base_config()
        # Qwen-specific optimizations
        config.update({
            "block_size": self.model_config.get("block_size", 16),
            "limit_mm_per_prompt": {"image": 10},  # Qwen can handle more images
        })
        return config


class GLMModelHandler(BaseModelHandler):
    """Handler for GLM model"""
        
    def get_vllm_config(self) -> Dict[str, Any]:
        config = self.get_base_config()
        # GLM-specific optimizations
        config.update({
            "block_size": self.model_config.get("block_size", 8),  # Smaller for GLM
            "limit_mm_per_prompt": {"image": 5},  # More conservative
        })
        
        # Add GLM-specific parameters
        if self.model_config.get("served_model_name"):
            config["served_model_name"] = self.model_config.served_model_name
            
        return config


class NvidiaModelHandler(BaseModelHandler):
    """Handler for NVIDIA models (Nemotron, etc.)"""
    
    def get_vllm_config(self) -> Dict[str, Any]:
        config = self.get_base_config()        
        config.update({
            "block_size": self.model_config.get("block_size", 16),
            "limit_mm_per_prompt": {"image": 6},  # Conservative for NVIDIA models
        })
        return config


class DoclingHandler(BaseModelHandler):
    """Handler for Smol models (SmolDocling, etc.)"""
        
    def get_vllm_config(self) -> Dict[str, Any]:
        config = self.get_base_config()
        config.update({
            "block_size": self.model_config.get("block_size", 8),
            "limit_mm_per_prompt": {"image": 12},  # Can handle more due to smaller size
        })
        return config