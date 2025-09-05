import hashlib
from pathlib import Path
from typing import List
from fastapi import APIRouter, File, UploadFile, Depends, Form
from sqlalchemy.orm import Session
from omegaconf import DictConfig
from app.config import get_config
from app import crud
from app.db import get_db
from pdf2image import convert_from_bytes
from app.logger import logger
from app.process import evaluate_candidate_and_create
from app.schemas import Resume, Outcome

router = APIRouter(
    prefix="/api/upload",
    tags=["upload"],
)

# TODO : add proper async support for the upload
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
    all_results = {Outcome.SUCCESS: 0, Outcome.LLM_ERROR: 0, Outcome.SERVER_ERROR: 0, Outcome.SKIPPED: 0}
    for _file in pdf_files:
        if not (_file.content_type == "application/pdf" and _file.filename and _file.filename.lower().endswith(".pdf")):
            logger.warning(f"Rejected invalid file: {_file.filename}")
            continue
        
        file_bytes = await _file.read()        
        resume_hash = hashlib.sha256(file_bytes).hexdigest()        
        file_url = store_file(cfg, file_bytes, f"{Path(_file.filename).stem}_{resume_hash[:8]}.pdf")
        resume = Resume(hash=resume_hash, resume_uri=file_url, is_invalid=False, images=[])
        job = crud.get_jobs(db_session, title=job_title)        
        resume_images = None
        try:
            resume_images = convert_from_bytes(file_bytes)[:cfg.app.max_page_size]
            logger.info(f"Converted {_file.filename} to {len(resume_images)} images.")    
            resume.images = resume_images
        except Exception as e:
            if isinstance(e, OSError) and "poppler" in str(e).lower():
                logger.error(f"Poppler is not installed or not found in PATH. Please install poppler to enable PDF to image conversion. Error: {e}")
                delete_file(cfg, resume.resume_uri)
                raise e

        logger.info(f"Checking if candidate exists by resume hash: {resume_hash}")
        candidate = crud.get_candidates(db_session, resume_hash=resume_hash)
        if candidate:
            logger.warning(f"Candidate {candidate.name} / {candidate.email} already exists with resume-hash:[{candidate.resume_hash}]. Checking if they have applied to this job.")            
            jobs_applied = crud.get_jobs_applied_by_candidate(db_session, candidate_id=candidate.id)            
            # check if candidate has applied to this job
            if jobs_applied is not None and job_title in [job.title for job in list(jobs_applied)]:
                logger.info(f"Skipping candidate {candidate.name} / {candidate.email} because they have already applied to this job: {job_title}")
                all_results[Outcome.SKIPPED] += 1
                continue    
            else:
                #  candidate exists but has not applied to this job
                logger.warning(f"Candidate {candidate.name} / {candidate.email} exists but has not applied to this job: {job_title}. Evaluating for this job.")
                result = await evaluate_candidate_and_create(cfg, job, db_session, resume, candidate=candidate)
                all_results[result.outcome] += 1
                if result.outcome == Outcome.SUCCESS:
                    processed_files.append(_file.filename)
        # candidate not found, create a new candidate and evaluate for this job
        else:
            logger.info(f"Candidate not found with resume-hash:[{resume_hash}]. Evaluating and creating new candidate...")                        
            result = await evaluate_candidate_and_create(cfg, job, db_session, resume)                                
            all_results[result.outcome] += 1
            if result.outcome == Outcome.SUCCESS:
                processed_files.append(_file.filename)
                        
                    
    return {
        "message": {
            "success": all_results[Outcome.SUCCESS],
            "llm_error": all_results[Outcome.LLM_ERROR],
            "server_error": all_results[Outcome.SERVER_ERROR],
            "skipped": all_results[Outcome.SKIPPED],
            "total": all_results[Outcome.SUCCESS] + all_results[Outcome.LLM_ERROR] + all_results[Outcome.SERVER_ERROR] + all_results[Outcome.SKIPPED]
        },
        "debug_message": f"{all_results[Outcome.SUCCESS]}/{len(pdf_files)} resumes processed and saved.",
        "processed_files": processed_files
    }



def store_file(cfg: DictConfig, file_bytes: bytes, filename: str) -> str:
    if cfg.app.env == "prod":
        raise NotImplementedError("Azure Blob Storage is not implemented yet. Only for prod environment.")
    else:
        return str(store_pdf_file_locally(cfg, file_bytes, filename))


def store_pdf_file_locally(cfg: DictConfig, file_bytes: bytes, filename: str) -> Path:
    file_path = Path(cfg.local_storage.path) / filename
    file_path.write_bytes(file_bytes)
    return file_path.resolve()


def delete_file(cfg: DictConfig, filename: str):
    if cfg.app.env == "prod":
        raise NotImplementedError("Azure Blob Storage is not implemented yet. Only for prod environment.")
    else:
        return delete_from_local_storage(cfg, filename)


def delete_from_local_storage(cfg: DictConfig, filename: str):    
    file_path = Path(cfg.local_storage.path) / filename
    file_path.unlink(missing_ok=True)
