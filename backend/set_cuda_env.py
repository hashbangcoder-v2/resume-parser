#!/usr/bin/env python3
"""
Script to set CUDA memory management environment variables for vLLM optimization.
Run this before starting the application to reduce CUDA memory fragmentation.
"""

import os
import subprocess
import sys

def set_cuda_env_vars():
    """Set CUDA environment variables for memory optimization."""
    env_vars = {
        'PYTORCH_CUDA_ALLOC_CONF': 'expandable_segments:True',
        'CUDA_VISIBLE_DEVICES': '0',  # Use only GPU 0
        'VLLM_USE_TRITON_FLASH_ATTN': 'false',  # Disable flash attention to save memory
        'VLLM_WORKER_MULTIPROC_METHOD': 'spawn',  # Use spawn method for multiprocessing
    }
    
    print("Setting CUDA environment variables for memory optimization:")
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"  {key}={value}")
    
    print("\nEnvironment variables set successfully!")
    return env_vars

if __name__ == "__main__":
    # Set environment variables
    env_vars = set_cuda_env_vars()
    
    # If additional arguments are provided, execute them with the new environment
    if len(sys.argv) > 1:
        print(f"\nExecuting: {' '.join(sys.argv[1:])}")
        # Update environment for subprocess
        env = os.environ.copy()
        env.update(env_vars)
        subprocess.run(sys.argv[1:], env=env)