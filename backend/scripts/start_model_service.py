#!/usr/bin/env python3
"""
Startup script for the Model Service
Run this to start the VLLM model service on port 8001
"""
import os
import sys
from pathlib import Path
import uvicorn

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set PROJECT_ROOT environment variable
os.environ["PROJECT_ROOT"] = str(backend_dir.parent)

if __name__ == "__main__":
    print("🚀 Starting Model Service on port 8001...")
    print("📍 This service handles VLLM model loading and inference")
    print("🔄 Hot-swapping capabilities enabled")
    print("=" * 50)
    
    uvicorn.run(
        "model_service:app",
        host="0.0.0.0",
        port=8001,
        reload=False,  # Disable reload for model service to avoid reloading large models
        log_level="info"
    )
