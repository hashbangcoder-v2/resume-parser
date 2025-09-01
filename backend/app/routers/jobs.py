from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Union, Optional
from app import crud, schemas
from app.db import get_db
from app.logger import logger

router = APIRouter(
    prefix="/api/jobs",
    tags=["jobs"],
)

@router.post("", response_model=schemas.Job)
def create_job(job: schemas.JobBase, db: Session = Depends(get_db)):
    logger.info(f"Creating job: {job}")
    db_job = crud.get_jobs(db, title=job.title)
    if db_job:
        raise HTTPException(status_code=400, detail="Job already exists")
    return crud.create_or_update_job(db=db, job=job)

@router.get("")
def read_jobs(job_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if job_id is not None:
        # Single job request using query parameter
        db_job = crud.get_job(db, job_id=job_id)
        if db_job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return db_job
    else:
        # Multiple jobs request
        jobs = crud.get_jobs(db, skip=skip, limit=limit)
        return jobs

# @router.get("/{job_id}", response_model=schemas.Job)
# def read_single_job(job_id: int, db: Session = Depends(get_db)):
#     # Single job request using path parameter (for backward compatibility)
#     db_job = crud.get_job(db, job_id=job_id)
#     if db_job is None:
#         raise HTTPException(status_code=404, detail="Job not found")
#     return db_job

@router.put("/{job_id}", response_model=schemas.Job)
def update_job(job_id: int, job: schemas.JobBase, db: Session = Depends(get_db)):
    logger.info(f"Updating job {job_id}: {job}")
    db_job = crud.create_or_update_job(db, job_id=job_id, job=job)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job


