#!/bin/bash

# A script to launch the entire development environment for the Wheat-From-Chaff application.

# Function to clean up background processes on exit
cleanup() {
    echo "Shutting down services..."
    kill $VLLM_PID $BACKEND_PID
    exit
}

# Trap SIGINT (Ctrl+C) and call the cleanup function
trap cleanup SIGINT
# Step 0: Activate venv
echo "--- Activating venv ---"
source backend/.venv/bin/activate

# 1. Start the vLLM Server
# echo "--- Starting local vLLM server in the background (port 8888) ---"
# # Assumes vLLM is installed in the global python environment or a sourced venv
# python -m vllm.entrypoints.openai.api_server \
#     --model Qwen/Qwen-VL-Chat \
#     --host 0.0.0.0 \
#     --port 8888 > vllm_server.log 2>&1 &
# VLLM_PID=$!
# echo "vLLM server started with PID: $VLLM_PID. Logs will be in vllm_server.log"
# sleep 15 # Give the model time to load

# 2. Start the FastAPI Backend
echo "--- Starting FastAPI backend ---"
export APP_ENV=dev

uv wfc-serve > logs/backend_server.log 2>&1 &
BACKEND_PID=$!
echo "FastAPI backend started with PID: $BACKEND_PID. Logs will be in logs/backend_server.log"
sleep 5 # Give the backend a moment to start up

# 3. Start the Next.js Frontend
echo "--- Starting Next.js frontend ---"
cd frontend
npm run dev

# Call cleanup when the frontend process exits
cleanup 