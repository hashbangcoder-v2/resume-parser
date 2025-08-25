
import hashlib
from pathlib import Path
from typing import List
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from omegaconf import DictConfig
from app.config import get_config
from app import crud, schemas
from app.db import get_db
from pdf2image import convert_from_bytes
from azure.storage.blob import BlobServiceClient
from app.logger import logger
from app.schemas import FinalStatus
from app.process import evaluate_candidate_and_create

router = APIRouter(
    prefix="/api/upload",
    tags=["upload"],
)

@router.post("")
async def upload_files(
    pdf_files: List[UploadFile] = File(...), 
    job_title: str = Form(...),
    db_session: Session = Depends(get_db),
    cfg: DictConfig = Depends(get_config)    
):
    """
    Upload a list of PDF files for a job and check if candidate exists using resume hash
    - if candidate exists, check if they have applied to this job
        - YES -> skip the candidate.
        - NO -> evaluate the candidate for this job and create a new application.

    - if candidate does not exist, create a new candidate, evaluate the candidate for this job and create a new application.     
    """
    logger.info(f"Uploading {len(pdf_files)} files for job: {job_title}")
    processed_files = []
    
    for _file in pdf_files:
        if not (_file.content_type == "application/pdf" and _file.filename and _file.filename.lower().endswith(".pdf")):
            logger.warning(f"Rejected invalid file: {_file.filename}")
            continue
        
        file_bytes = await _file.read()        
        resume_hash = hashlib.sha256(file_bytes).hexdigest()        
        job = crud.get_jobs(db_session, title=job_title)        
        resume_images = None
        try:
            resume_images = convert_from_bytes(file_bytes)[:cfg.app.max_page_size]
            logger.info(f"Converted {_file.filename} to {len(resume_images)} images.")            
        except Exception as e:
            if isinstance(e, OSError) and "poppler" in str(e).lower():
                logger.error(f"Poppler is not installed or not found in PATH. Please install poppler to enable PDF to image conversion. Error: {e}")
                raise e

        logger.info(f"Checking if candidate exists by resume hash: {resume_hash}")
        candidate = crud.get_candidates(db_session, resume_hash=resume_hash)
        if candidate:
            logger.warning(f"Candidate {candidate.name} / {candidate.email} already exists with resume-hash:[{candidate.resume_hash}]. Checking if they have applied to this job.")            
            jobs_applied = crud.get_jobs_applied_by_candidate(db_session, candidate_id=candidate.id)            
            # check if candidate has applied to this job
            if jobs_applied is not None and job_title in [job.title for job in list(jobs_applied)]:
                logger.info(f"Skipping candidate {candidate.name} / {candidate.email} because they have already applied to this job: {job_title}")
                continue    
            else:
                #  candidate exists but has not applied to this job
                logger.warning(f"Candidate {candidate.name} / {candidate.email} exists but has not applied to this job: {job_title}. Evaluating for this job.")
                llm_response = await evaluate_candidate_and_create(cfg, resume_images, job, db_session, resume_hash, candidate=candidate)
                processed_files.append(_file.filename)
        # candidate not found, create a new candidate and evaluate for this job
        else:
            logger.info(f"Candidate not found with resume-hash:[{resume_hash}]. Evaluating and creating new candidate...")                        
            llm_response = await evaluate_candidate_and_create(cfg, resume_images, job, db_session, resume_hash)                    
            processed_files.append(_file.filename)
            
        file_url = store_file(cfg, file_bytes, f"{Path(_file.filename).stem}_{resume_hash[:8]}.pdf")
        
            
    if not processed_files:
        return {"message": "No new valid PDF files were processed."}, 400
    
    return {
        "message": f"{len(processed_files)}/{len(pdf_files)} resumes processed and saved.",
        "processed_files": processed_files
    }



def store_file(cfg: DictConfig, file_bytes: bytes, filename: str) -> str:
    if cfg.app.env == "prod":
        return upload_to_azure_blob(cfg, file_bytes, filename)
    else:
        return str(store_pdf_file_locally(cfg, file_bytes, filename))

def upload_to_azure_blob(cfg: DictConfig, file_bytes: bytes, filename: str) -> str:
    try:
        connection_string = cfg.azure_blob.connection_string
        container_name = cfg.azure_blob.container_name
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename)
        blob_client.upload_blob(file_bytes, overwrite=True)
        return blob_client.url
    except Exception as e:
        logger.error(f"Failed to upload to Azure Blob Storage: {e}")
        return ""

def store_pdf_file_locally(cfg: DictConfig, file_bytes: bytes, filename: str) -> Path:
    save_dir = Path(cfg.local_storage.path)
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / filename
    file_path.write_bytes(file_bytes)
    return file_path.resolve()