from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
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
    return crud.create_job(db=db, job=job)

@router.get("", response_model=List[schemas.Job])
def read_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    jobs = crud.get_jobs(db, skip=skip, limit=limit)
    return jobs

@router.get("/{job_id}", response_model=schemas.Job)
def read_job(job_id: int, db: Session = Depends(get_db)):
    db_job = crud.get_job(db, job_id=job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job


