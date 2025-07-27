import logging
import tempfile
import hashlib
from pathlib import Path
from pdf2image import convert_from_bytes
from typing import List, Dict
from fastapi import APIRouter, File, UploadFile, Depends
from sqlalchemy.orm import Session
from ..config import cfg, DictConfig
from .. import schemas, db, llm_client
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/upload",
    tags=["upload"],
)

@router.post("/")
async def upload_files(pdf_files: List[UploadFile] = File(...), db_session: Session = Depends(db.get_db)):
    accepted_files = []
    processed_candidates = []
    
    for file in pdf_files:
        if not (file.content_type == "application/pdf" and file.filename.lower().endswith(".pdf")):
            logger.warning(f"Rejected invalid file: {file.filename}")
            continue
        
        accepted_files.append(file.filename)
        file_bytes = await file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()[:8]
        hashed_filename = f"{Path(file.filename).stem}_{file_hash}"

        file_url = ""
        if cfg.APP_ENV == "prod":
            file_url = upload_to_azure_blob(file_bytes, hashed_filename, cfg)
        else:
            file_url = str(store_pdf_file_locally(file_bytes, hashed_filename, cfg))

        if not file_url:
            logger.error(f"Failed to store file: {file.filename}")
            continue

        try:
            images = convert_from_bytes(file_bytes)
            logger.info(f"Converted {file.filename} to {len(images)} images.")
            
            # Call the LLM to get an analysis
            llm_response = await llm_client.get_model_response(cfg, images)
            
            # --- Placeholder for parsing the LLM response ---
            # In a real app, you would have robust logic to parse the llm_response
            # For now, we'll use mock data and the filename
            analysis_result = {
                "name": Path(file.filename).stem.replace("_", " ").title(),
                "status": "Needs Review",
                "reason": llm_response.get('choices', [{}])[0].get('message', {}).get('content', 'AI analysis pending.'),
                "finalStatus": "Needs Review",
                "jobTitle": "Software Engineer" # Default or extracted from context
            }
            # --- End Placeholder ---
            
            # Create a new candidate record in the database
            new_candidate = db.Candidate(
                name=analysis_result["name"],
                status=analysis_result["status"],
                reason=analysis_result["reason"],
                finalStatus=analysis_result["finalStatus"],
                jobTitle=analysis_result["jobTitle"],
                fileUrl=file_url,
            )
            db_session.add(new_candidate)
            db_session.commit()
            db_session.refresh(new_candidate)
            processed_candidates.append(new_candidate.name)
            
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            db_session.rollback()
            continue
            
    if not accepted_files:
        return {"message": "No valid PDF files were uploaded."}, 400
    
    return {
        "message": f"{len(processed_candidates)}/{len(pdf_files)} resumes processed and saved.",
        "processed_candidates": processed_candidates
    }, 201

def upload_to_azure_blob(file_bytes: bytes, filename: str, cfg: DictConfig) -> str:
    try:
        connection_string = cfg.azure_blob.connection_string
        container_name = cfg.azure_blob.container_name
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=f"{filename}.pdf")
        blob_client.upload_blob(file_bytes, overwrite=True)
        return blob_client.url
    except Exception as e:
        logger.error(f"Failed to upload to Azure Blob Storage: {e}")
        return ""

def store_pdf_file_locally(file_bytes: bytes, filename: str, cfg: DictConfig) -> Path:
    save_dir = Path(cfg.local_storage.path)
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / f"{filename}.pdf"
    file_path.write_bytes(file_bytes)
    return file_path.resolve()