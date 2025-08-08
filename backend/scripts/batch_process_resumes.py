import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from backend.app.config import get_config
from backend.app.db import get_db
from backend.app.models import Application, Job
from backend.app.crud import update_application_status_and_reason
from backend.app import llm_client
from sqlalchemy.orm import Session
from loguru import logger
from pdf2image import convert_from_path

def process_unprocessed_applications(db: Session, model_name: Optional[str] = None, batch_size: int = 10):
    """
    Fetches and processes applications that have not yet been analyzed by the LLM.
    """
    unprocessed_apps = db.query(Application).filter(Application.status == "Needs Review").limit(batch_size).all()
    
    if not unprocessed_apps:
        logger.info("No applications to process.")
        return

    logger.info(f"Found {len(unprocessed_apps)} applications to process.")

    cfg = get_config()

    for app in unprocessed_apps:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        if not job:
            logger.warning(f"Job not found for application {app.id}, skipping.")
            continue

        resume_path = Path(app.file_url)
        if not resume_path.exists():
            logger.warning(f"Resume file not found for application {app.id} at {resume_path}, skipping.")
            continue

        try:
            images = convert_from_path(resume_path)
            llm_response = asyncio.run(llm_client.get_model_response(cfg, images, job.description, model_name))
            
            update_application_status_and_reason(db, application_id=app.id, status=llm_response.outcome.value, reason=llm_response.reason)
            logger.info(f"Processed and updated application {app.id} with outcome: {llm_response.outcome.value}")

        except Exception as e:
            logger.error(f"Failed to process application {app.id}: {e}")
            update_application_status_and_reason(db, application_id=app.id, status="Needs Review", reason=f"Failed to process: {e}")

def main(model_name: Optional[str] = None, batch_size: int = 10):
    """
    Main function to run the batch processing script.
    """
    logger.info("Starting batch resume processing...")
    db = next(get_db())
    try:
        process_unprocessed_applications(db, model_name, batch_size)
    finally:
        db.close()
    logger.info("Batch processing complete.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Batch process resumes using an LLM.")
    parser.add_argument("--model", type=str, help="The name of the model to use for processing.")
    parser.add_argument("--batch-size", type=int, default=10, help="The number of applications to process in each batch.")
    args = parser.parse_args()

    if "PROJECT_ROOT" not in os.environ:
        os.environ["PROJECT_ROOT"] = str(project_root)

    main(model_name=args.model, batch_size=args.batch_size) 