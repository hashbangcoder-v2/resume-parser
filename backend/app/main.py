from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import jobs, applications, status, user, upload
from app.db import engine, Base
import sys
import logging
import uvicorn

from app import models
from app.config import get_config
from app.logger import setup_logging
from app.llm_client import initialize_vllm

cfg = get_config()
setup_logging(cfg)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Initialize vLLM model on startup if in dev mode
if cfg.app.env != "prod":
    initialize_vllm(cfg)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.app.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(status.router)
app.include_router(user.router)
app.include_router(upload.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Wheat-From-Chaff API"}

def main():
    uvicorn.run(
        "app.main:app",
        host=cfg.app.host,
        port=cfg.app.port,
        reload=cfg.app.env == "dev",  # Reload only in dev
        log_config=None,
        access_log=True,
    )
