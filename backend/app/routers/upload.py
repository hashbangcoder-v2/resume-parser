import logging
import hashlib
from pathlib import Path
from typing import List
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from omegaconf import DictConfig
from app.config import get_config
from app import crud, schemas, models
from app.db import get_db
from pdf2image import convert_from_bytes
from app import llm_client
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/upload",
    tags=["upload"],
)

@router.post("/")
async def upload_files(
    pdf_files: List[UploadFile] = File(...), 
    db_session: Session = Depends(get_db),
    cfg: DictConfig = Depends(get_config)
):
    processed_files = []
    
    for file in pdf_files:
        if not (file.content_type == "application/pdf" and file.filename and file.filename.lower().endswith(".pdf")):
            logger.warning(f"Rejected invalid file: {file.filename}")
            continue
        
        file_bytes = await file.read()
        resume_hash = hashlib.sha256(file_bytes).hexdigest()

        # In a real app, you would parse the resume to get the email.
        # For now, we'll generate a placeholder email from the filename.
        email = f"{Path(file.filename).stem}@example.com"

        # Check if candidate exists by email or resume hash
        candidate = crud.get_candidate_by_email(db_session, email=email)
        if not candidate:
            # In a real app, name would be parsed from the resume.
            name = Path(file.filename).stem.replace("_", " ").title()
            candidate_in = schemas.CandidateCreate(name=name, email=email, resume_hash=resume_hash)
            candidate = crud.create_candidate(db_session, candidate=candidate_in)
        
        # --- LLM Analysis ---
        try:
            images = convert_from_bytes(file_bytes)
            logger.info(f"Converted {file.filename} to {len(images)} images.")
            llm_response = await llm_client.get_model_response(cfg, images)
            analysis_result = llm_response.get('choices', [{}])[0].get('message', {}).get('content', 'AI analysis pending.')
        except Exception as e:
            logger.error(f"Failed to process {file.filename} with LLM: {e}")
            analysis_result = "Error during AI analysis."
        # --- End LLM Analysis ---

        # For now, we assume a default job title. This could be passed as a parameter.
        job_title = "Senior Software Engineer"
        job = crud.get_job_by_title(db_session, title=job_title)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_title}' not found.")

        # Check if an application already exists
        application_exists = db_session.query(models.Application).filter_by(candidate_id=candidate.id, job_id=job.id).first()
        if application_exists:
            logger.warning(f"Skipping duplicate application for {candidate.email} to {job.title}")
            continue

        file_url = store_file(cfg, file_bytes, f"{Path(file.filename).stem}_{resume_hash[:8]}.pdf")

        application_in = schemas.ApplicationCreate(
            job_id=job.id,
            candidate_id=candidate.id,
            status="Needs Review",
            final_status="Needs Review",
            reason=analysis_result,
            file_url=file_url,
        )
        crud.create_application(db_session, application=application_in)
        processed_files.append(file.filename)
            
    if not processed_files:
        return {"message": "No new valid PDF files were processed."}, 400
    
    return {
        "message": f"{len(processed_files)}/{len(pdf_files)} resumes processed and saved.",
        "processed_files": processed_files
    }

def store_file(cfg: DictConfig, file_bytes: bytes, filename: str) -> str:
    if cfg.APP_ENV == "prod":
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