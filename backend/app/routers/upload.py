
import hashlib
from pathlib import Path
from typing import List
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from omegaconf import DictConfig
from app.config import get_config
from app import crud, schemas, models
from app.db import get_db
from pdf2image import convert_from_bytes
from app import llm_client
from azure.storage.blob import BlobServiceClient
from app.logger import logger


from app.process import reevaluate_candidate, evaluate_candidate

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
    logger.info(f"Uploading {len(pdf_files)} files for job: {job_title}")
    processed_files = []
    
    for _file in pdf_files:
        if not (_file.content_type == "application/pdf" and _file.filename and _file.filename.lower().endswith(".pdf")):
            logger.warning(f"Rejected invalid file: {_file.filename}")
            continue
        
        file_bytes = await _file.read()
        resume_hash = hashlib.sha256(file_bytes).hexdigest()


        # --- LLM Analysis ---
        try:
            images = convert_from_bytes(file_bytes)
            logger.info(f"Converted {_file.filename} to {len(images)} images.")
            
            job = crud.get_job_by_title(db_session, title=job_title)
            if not job:
                raise HTTPException(status_code=404, detail=f"Job '{job_title}' not found.")

            llm_response = await llm_client.get_model_response(cfg, images, job.description)
            analysis_result = llm_response.reason
            final_status = schemas.LLMOutcome(llm_response.outcome).value

        except Exception as e:
            if isinstance(e, OSError) and "poppler" in str(e).lower():
                logger.error(f"Poppler is not installed or not found in PATH. Please install poppler to enable PDF to image conversion. Error: {e}")
                raise e
            
            logger.error(f"Failed to process {_file.filename} with LLM: {e}", exc_info=True)
            analysis_result = "Error during AI analysis."
            final_status = schemas.LLMOutcome.FAILED.value


        if final_status != schemas.LLMOutcome.FAILED.value:
            name = llm_response.name
            email = llm_response.email
            logger.info(f"Extracted name: {name} and email: {email} from {_file.filename}")
            

        logger.info(f"Checking if candidate exists by resume hash: {resume_hash}")
        candidate = crud.get_candidates(db_session, resume_hash=resume_hash)
        if candidate:
            logger.warning(f"Candidate {candidate.name} already exists: {candidate.email} {candidate.resume_hash}")            
            jobs_applied = crud.get_jobs_applied_by_candidate(db_session, candidate_id=candidate.id)
            logger.warning(f"Candidate {candidate.name} has already applied to {len(jobs_applied)} jobs: {jobs_applied}")
            if jobs_applied is not None and job_title in [job.title for job in list(jobs_applied)]:
                logger.info(f"Skipping candidate {candidate.name} because they have already applied to this job")
                continue    
            else:
                logger.info(f"Re-evaluating candidate {candidate.name} for this job: {job_title}")
                job = crud.get_job_by_title(db_session, title=job_title)
                if not job:
                    logger.warning(f"Job '{job_title}' not found when re-evaluating candidate.")
                    raise HTTPException(status_code=404, detail=f"Job '{job_title}' not found.")
                
                reevaluate_candidate(cfg, candidate, job.description, file_bytes)


        else:
            logger.warning(f"Candidate not found: {resume_hash}")
            
            
            candidate_in = schemas.CandidateCreate(name=name, email=email, resume_hash=resume_hash)
            # candidate = crud.create_candidate(db_session, candidate=candidate_in)
        
        # Check if an application already exists
        application_exists = db_session.query(models.Application).filter_by(candidate_id=candidate.id, job_id=job.id).first()
        if application_exists:
            logger.warning(f"Skipping duplicate application for {candidate.email} to {job.title}")
            continue

        file_url = store_file(cfg, file_bytes, f"{Path(_file.filename).stem}_{resume_hash[:8]}.pdf")

        application_in = schemas.ApplicationCreate(
            job_id=job.id,
            candidate_id=candidate.id,
            status=schemas.ApplicationStatus.NEEDS_REVIEW,
            final_status=final_status,
            reason=analysis_result,
            file_url=file_url,
        )
        crud.create_application(db_session, application=application_in)
        processed_files.append(_file.filename)
            
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