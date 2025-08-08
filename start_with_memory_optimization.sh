#!/bin/bash

# Script to start the application with CUDA memory optimizations
# This script sets environment variables and starts the backend service

echo "🚀 Starting Wheat-from-Chaff with CUDA memory optimizations..."

# Set CUDA memory optimization environment variables
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_VISIBLE_DEVICES=0
export VLLM_USE_TRITON_FLASH_ATTN=false
export VLLM_WORKER_MULTIPROC_METHOD=spawn

echo "📋 Environment variables set:"
echo "  PYTORCH_CUDA_ALLOC_CONF=$PYTORCH_CUDA_ALLOC_CONF"
echo "  CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "  VLLM_USE_TRITON_FLASH_ATTN=$VLLM_USE_TRITON_FLASH_ATTN"
echo "  VLLM_WORKER_MULTIPROC_METHOD=$VLLM_WORKER_MULTIPROC_METHOD"

# Check GPU memory before starting
echo "🔍 GPU Memory Status before starting:"
nvidia-smi --query-gpu=memory.total,memory.free,memory.used --format=csv,noheader,nounits

# Change to backend directory
cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found at backend/.venv"
    echo "Please run the setup first."
    exit 1
fi

# Activate virtual environment and start the application
echo "🏃 Starting the backend service..."
source .venv/bin/activate
python -m app.main

echo "✅ Application started successfully!"