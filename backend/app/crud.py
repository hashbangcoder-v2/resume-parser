from sqlalchemy.orm import Session
from app import models, schemas

# Job CRUD
def get_job(db: Session, job_id: int):
    return db.query(models.Job).filter(models.Job.id == job_id).first()

def get_job_by_title(db: Session, title: str):
    return db.query(models.Job).filter(models.Job.title == title).first()

def get_jobs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Job).offset(skip).limit(limit).all()

def create_job(db: Session, job: schemas.JobCreate):
    db_job = models.Job(title=job.title, description=job.description)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

# Candidate CRUD

def get_candidates(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    email: str = None,
    resume_hash: str = None,
    match_both: bool = False,
):
    """
    Retrieve candidates with optional filters:
    - If both email and resume_hash are provided and match_either is True, return the first candidate matching either.
    - If both are provided and match_either is False, return candidates matching both.
    - If only one is provided, filter by that.
    - If neither is provided, return all candidates paginated.
    """
    query = db.query(models.Candidate)
    if email is not None and resume_hash is not None:
        if not match_both:
            candidate = (
                query.filter(
                    (models.Candidate.resume_hash == resume_hash)                     
                )
                .first()
            )
            return candidate
        else:
        
            return (
                query.filter(
                    (models.Candidate.resume_hash == resume_hash) & (models.Candidate.email == email)                  
                )
                .offset(skip)
                .limit(limit)
                .all()
            )
    elif resume_hash is not None:
        return query.filter(models.Candidate.resume_hash == resume_hash).offset(skip).limit(limit).all()
    elif email is not None:
        return query.filter(models.Candidate.email == email).offset(skip).limit(limit).all()
    else:
        return query.offset(skip).limit(limit).all()

def get_jobs_applied_by_candidate(db: Session, candidate_id: int):
    return (
        db.query(models.Job)
        .join(models.Application, models.Application.job_id == models.Job.id)
        .filter(models.Application.candidate_id == candidate_id)
        .all()
    )

def create_candidate(db: Session, candidate: schemas.CandidateCreate):
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