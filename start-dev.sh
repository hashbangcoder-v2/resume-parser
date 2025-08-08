#!/bin/bash

# A script to launch the entire development environment for the Wheat-From-Chaff application.

# Function to clean up background processes on exit
cleanup() {
    echo "Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID
    fi
    exit
}

# Trap SIGINT (Ctrl+C) and call the cleanup function
trap cleanup SIGINT

# --- Environment Setup ---
# Source system-wide environment variables to ensure cache paths are set
if [ -f /etc/environment ]; then
    echo "--- Sourcing /etc/environment for cache paths ---"
    export $(grep -v '^#' /etc/environment | xargs)
else
    echo "[WARNING] /etc/environment not found. Cache paths may not be set correctly."
fi

# Activate Python virtual environment
echo "--- Activating venv ---"
source backend/.venv/bin/activate

# --- Start Services ---
# Start the FastAPI Backend
echo "--- Starting FastAPI backend ---"
export APP_ENV=dev
export PROJECT_ROOT=$(pwd) # Export for config loading

uvicorn --host 0.0.0.0 --port 8000 --reload app.main:app > logs/backend_server.log 2>&1 &
BACKEND_PID=$!
echo "FastAPI backend started with PID: $BACKEND_PID. Logs will be in logs/backend_server.log"
sleep 15 # Give the backend and model time to start up

# Start the Next.js Frontend
echo "--- Starting Next.js frontend ---"
cd frontend
npm run dev

# Call cleanup when the frontend process exits
cleanup
