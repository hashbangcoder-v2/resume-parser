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
def get_candidate(db: Session, candidate_id: int):
    return db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()

def get_candidate_by_email(db: Session, email: str):
    return db.query(models.Candidate).filter(models.Candidate.email == email).first()

def get_candidates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Candidate).offset(skip).limit(limit).all()

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
    db_application = models.Application(**application.dict())
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