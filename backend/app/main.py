from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import jobs, applications, status, user, upload, models
from app.db import engine, Base
import logging
import uvicorn

from app import models as db_models
from app.config import get_config
from app.logger import setup_logging

cfg = get_config()
setup_logging(cfg)

db_models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI startup and shutdown events"""
    # Startup - Model service handles VLLM initialization 
    logging.info("FastAPI server starting - Model service handles VLLM")
    
    yield
    

app = FastAPI(lifespan=lifespan)

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
app.include_router(models.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Needle-in-a-Haystack API"}

def main():
    uvicorn.run(
        "app.main:app",
        host=cfg.app.host,
        port=cfg.app.port,
        reload=cfg.app.env == "dev",
        log_config=None,
        access_log=True,
    )
