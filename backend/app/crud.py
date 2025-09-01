from sqlalchemy.orm import Session
from app import db_models as models, schemas
from datetime import datetime

def get_jobs(db: Session, job_id: int = None, title: str = None, skip: int = 0, limit: int = 100):
    """
    Retrieve jobs with optional filters:
    - If job_id is provided, return the job with that id.
    - If title is provided, return the job with that title.
    - If neither is provided, return all jobs paginated.
    """
    query = db.query(models.Job)
    if job_id is not None:
        return query.filter(models.Job.id == job_id).first()
    elif title is not None:
        return query.filter(models.Job.title == title).first()
    else:
        return query.offset(skip).limit(limit).all()

def get_job(db: Session, job_id: int):
    """
    Get a single job by ID.
    """
    return db.query(models.Job).filter(models.Job.id == job_id).first()

def create_or_update_job(db: Session, job: schemas.JobBase, job_id: int = None):
    """
    Create a new job or update an existing one.
    - If job_id is None, creates a new job
    - If job_id is provided, updates the existing job
    """
    if job_id is None:
        # Create new job
        db_job = models.Job(title=job.title, description=job.description, created_at=datetime.now())
        db.add(db_job)
    else:
        # Update existing job
        db_job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if db_job:
            db_job.title = job.title
            db_job.description = job.description
    
    if db_job:
        db.commit()
        db.refresh(db_job)
    return db_job


def get_candidates(
    db: Session,
    limit: int = 100,
    email: str = None,
    resume_hash: str = None,    
) -> models.Candidate | list[models.Candidate]:
    """
    Retrieve candidates with optional filters:
    - If resume_hash is provided, return the first candidate matching .
    - If only email is provided, filter by that.
    - If neither is provided, return all candidates paginated upto limit
    """
    query = db.query(models.Candidate)
    if resume_hash is not None:
        return query.filter(models.Candidate.resume_hash == resume_hash).first()
    elif email is not None:
        return query.filter(models.Candidate.email == email).first()
    else:
        return query.limit(limit).all()

    
def get_jobs_applied_by_candidate(db: Session, candidate_id: int):
    """
    Get all jobs applied by a candidate.
    """
    return (
        db.query(models.Job)
        .join(models.Application, models.Application.job_id == models.Job.id)
        .filter(models.Application.candidate_id == candidate_id)
        .all()
    )

def create_candidate(db: Session, candidate: schemas.CandidateCreate):
    """
    Create a new candidate.
    """
    db_candidate = models.Candidate(name=candidate.name, email=candidate.email, resume_hash=candidate.resume_hash)
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate


# Application CRUD
def get_applications_for_job(db: Session, job_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Application).filter(models.Application.job_id == job_id).offset(skip).limit(limit).all()

def create_application(db: Session, application: schemas.ApplicationCreate):
    db_application = models.Application(**application.model_dump())
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

def update_application_status(db: Session, application_id: int, status: schemas.ApplicationUpdate):
    db_application = db.query(models.Application).filter(models.Application.id == application_id).first()
    if db_application:
        db_application.final_status = status.final_status
        db.commit()
        db.refresh(db_application)
    return db_application 