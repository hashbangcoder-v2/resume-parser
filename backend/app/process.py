import base64
import httpx
from PIL import Image
from typing import List
from omegaconf import DictConfig
from io import BytesIO

from app.logger import logger
from app import crud, schemas, process
from app.schemas import FinalStatus
from sqlalchemy.orm import Session
from app.schemas import LLMResponse
from app.config import get_config
from app import db_models


cfg = get_config()
MODEL_SERVICE_URL = cfg.model_service.url


def _encode_images_to_base64(images: List[Image.Image]) -> List[str]:
    """Convert PIL Images to base64 strings"""
    encoded_images = []
    for img in images:
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        encoded_images.append(img_str)
    return encoded_images


async def get_model_response(
    cfg: DictConfig, 
    images: List[Image.Image], 
    job_description: str, 
) -> LLMResponse:    
    """
    Get model response from the model service.
    This replaces the direct VLLM inference and maintains backward compatibility.
    """
    if cfg.app.env == "prod":
        return await query_azure_ml_endpoint() 
    else:
        return await query_model_service(images, job_description)


async def query_model_service(
    images: List[Image.Image], 
    job_description: str,     
) -> LLMResponse:
    """
    Performs inference via the model service (replaces query_vllm).
    """
    try:
        # Encode images to base64
        images_b64 = _encode_images_to_base64(images)
        
        # Prepare request payload
        request_data = {
            "images_b64": images_b64,
            "job_description": job_description
        }
        
        logger.info(f"Sending inference request with {len(images)} images to model service")
        
        # Call model service
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5-minute timeout for inference
            response = await client.post(
                f"{MODEL_SERVICE_URL}/inference",
                json=request_data
            )
            
            if response.status_code == 200:
                result_data = response.json()
                logger.info(f"Model service returned result: {result_data.get('outcome', 'Unknown')}")
                return LLMResponse(**result_data)
            elif response.status_code == 503:
                logger.warning("Model service unavailable (swapping?)")
                return LLMResponse(
                    outcome="Failed", 
                    reason="Model service temporarily unavailable (may be swapping models)"
                )
            else:
                logger.error(f"Model service error: {response.status_code} - {response.text}")
                return LLMResponse(
                    outcome="Failed", 
                    reason=f"Model service error: {response.status_code}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to model service: {e}")
        return LLMResponse(
            outcome="Failed", 
            reason="Failed to connect to model service"
        )
    except Exception as e:
        logger.error(f"Unexpected error in model service communication: {e}")
        return LLMResponse(
            outcome="Failed", 
            reason="Unexpected error during model inference"
        )


async def check_model_service_health() -> bool:
    """Check if model service is healthy"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{MODEL_SERVICE_URL}/health")
            return response.status_code == 200
    except:
        return False


async def query_azure_ml_endpoint() -> LLMResponse:
    """
    Queries the Azure ML Online Endpoint.
    """
    raise NotImplementedError("Azure ML Online Endpoint is not implemented yet.")


def _generate_unique_placeholder_email(resume_hash: str) -> str:
    """Generate a unique placeholder email for invalid document scenarios"""
    return f"invalid.email.{resume_hash[:8]}@candidate.blah"


async def evaluate_candidate_and_create(cfg: DictConfig, job: db_models.Job, db_session: Session, resume: schemas.Resume, candidate: db_models.Candidate = None):        
    try:
        llm_response = await process.get_model_response(cfg, resume.images, job.description)
        if llm_response.outcome != schemas.LLMOutcome.FAILED.value and llm_response.outcome != schemas.LLMOutcome.INVALID.value:        
            # candidate does not exist, create new candidate and application
            if candidate is None:
                logger.info(f"LLM evaluated candidate [resume-hash:{resume.hash}]: {llm_response.outcome} : {llm_response.reason}")
                
                # Handle placeholder emails to avoid unique constraint violations
                email = llm_response.email
                if email.lower() in ['n/a', 'na', 'not available', 'null', 'none', ''] or not '@' in email:
                    email = _generate_unique_placeholder_email(resume.hash)
                    logger.warning(f"LLM returned placeholder email '{llm_response.email}', using unique placeholder: {email}")
                
                candidate_new = schemas.Candidate(name=llm_response.name, email=email, resume_hash=resume.hash)
                logger.debug(f"Creating new candidate: {candidate_new}; llm_response: {llm_response}")
                candidate = crud.create_candidate(db_session, candidate=candidate_new)
            else:
            # candidate exists, create new application only
                logger.info(f"LLM evaluated existing candidate [resume-hash:{resume.hash}]: {llm_response.outcome} : {llm_response.reason}")
            application_in = schemas.ApplicationCreate(candidate_id=candidate.id, job_id=job.id, status=llm_response.outcome, final_status=FinalStatus.TBD, reason=llm_response.reason, file_uri=resume.resume_uri)
            crud.create_application(db_session, application=application_in)

        elif llm_response.outcome == schemas.LLMOutcome.INVALID.value:
            logger.warning(f"LLM evaluated candidate [resume-hash:{resume.hash}]: {llm_response.outcome} : {llm_response.reason}")                
            application_in = schemas.InvalidApplicationCreate(job_id=job.id, status=llm_response.outcome, reason=llm_response.reason, file_uri=resume.resume_uri)
            crud.create_application(db_session, application=application_in)
            return schemas.ProcessOutcome(outcome=schemas.Outcome.SUCCESS, message=f"{llm_response.outcome} : {llm_response.reason}")
        else:
            # application_in = schemas.ApplicationCreate(candidate_id=candidate.id, job_id=job.id, status=llm_response.outcome, final_status=FinalStatus.FAILED, reason=llm_response.reason, file_uri=resume.resume_uri)
            # crud.create_application(db_session, application=application_in)
            logger.error(f"[LLM ERROR] failed to evaluate candidate [resume-hash:{resume.hash}]: {llm_response.outcome} : {llm_response.reason}")        
            return schemas.ProcessOutcome(outcome=schemas.Outcome.LLM_ERROR, message=f"{llm_response.outcome} : {llm_response.reason}")
        return schemas.ProcessOutcome(outcome=schemas.Outcome.SUCCESS, message=f"{llm_response.outcome} : {llm_response.reason}")
    except Exception as e:
        logger.error(f"Failed to evaluate candidate and create application: {e}")
        return schemas.ProcessOutcome(outcome=schemas.Outcome.SERVER_ERROR, message=f"{e}")



