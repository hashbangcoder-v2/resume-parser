from app.schemas import Candidate
from app.config import DictConfig
from app.logger import logger
from fastapi import HTTPException
from pdf2image import convert_from_bytes
from app import llm_client


def process_upload(cfg: DictConfig, candidate: Candidate, job_description: str, file_bytes: bytes):
    
    pass


async def evaluate_candidate(cfg: DictConfig, candidate: Candidate, job_description: str, file_bytes: bytes):
    try:
        images = convert_from_bytes(file_bytes)
        logger.info(f"Converted {file.filename} to {len(images)} images.")
        llm_response = await llm_client.get_model_response(cfg, images)
        analysis_result = llm_response.get('choices', [{}])[0].get('message', {}).get('content', 'AI analysis pending.')
    except Exception as e:
        logger.error(f"Failed to process {file.filename} with LLM: {e}")
        raise HTTPException(status_code=500, detail=f"Error during AI analysis: {e}")

def reevaluate_candidate(cfg: DictConfig, candidate: Candidate, job_description: str, file_bytes: bytes):
    analysis = evaluate_candidate(cfg, candidate, job_description, file_bytes)
    pass
