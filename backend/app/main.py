from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import jobs, applications, status, user, upload
from app.db import engine, Base
import sys
import logging
import uvicorn

from app import models
from app.config import get_config

cfg = get_config()

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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
    logger = logging.getLogger(__name__)
    # Set up logging to file for uvicorn stdout and stderr
    # logging.basicConfig(
    #     level=cfg.logging.level.upper(),
    #     format="%(asctime)s %(levelname)s %(message)s",
    #     handlers=[
    #         logging.FileHandler("logs/uvicorn_stdout.log"),
    #         logging.StreamHandler(sys.stdout)
    #     ]
    # )
    logger.info("Starting uvicorn server at %s:%s", cfg.app.host, cfg.app.port)
    uvicorn.run(
        "app.main:app",
        host=cfg.app.host,
        port=cfg.app.port,
        reload=True,
        log_config=None,
        access_log=True,
    )