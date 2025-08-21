from PIL import Image
from typing import List
from app.config import DictConfig
from app.logger import logger
from app import llm_client, crud, schemas
from app.schemas import FinalStatus
from sqlalchemy.orm import Session
from app.models import Job, Candidate


def process_upload(cfg: DictConfig, candidate: Candidate, job_description: str, file_bytes: bytes):
    
    pass


async def evaluate_candidate_and_create(cfg: DictConfig, images: List[Image.Image], job: Job, db_session: Session, resume_hash: str, new_candidate: bool = False):    
    llm_response = await llm_client.get_model_response(cfg, images, job.description)
    if llm_response.outcome != schemas.LLMOutcome.FAILED.value:        
        if new_candidate:
            logger.info(f"LLM evaluated candidate [resume-hash:{resume_hash}]: {llm_response.outcome}")
            candidate_new = schemas.CandidateCreate(name=llm_response.name, email=llm_response.email, resume_hash=resume_hash)
            candidate = crud.create_candidate(db_session, candidate=candidate_new)
    
        application_in = schemas.ApplicationCreate(candidate_id=candidate.id, job_id=job.id, status=llm_response.outcome, final_status=FinalStatus.TBD, reason=llm_response.reason)
        crud.create_application(db_session, application=application_in)

    else:
        application_in = schemas.ApplicationCreate(candidate_id=candidate.id, job_id=job.id, status=llm_response.outcome, final_status=FinalStatus.FAILED, reason=llm_response.reason)
        crud.create_application(db_session, application=application_in)
        logger.error(f"LLM failed to evaluate candidate [resume-hash:{resume_hash}]: {llm_response.reason}")        




