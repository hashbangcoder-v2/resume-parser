from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Job Schemas
class JobBase(BaseModel):
    title: str
    description: Optional[str] = None

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Candidate Schemas
class CandidateBase(BaseModel):
    name: str
    email: str
    resume_hash: Optional[str] = None

class CandidateCreate(CandidateBase):
    pass

class Candidate(CandidateBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Application Schemas
class ApplicationBase(BaseModel):
    status: str
    final_status: str
    reason: Optional[str] = None
    file_url: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    job_id: int
    candidate_id: int

class ApplicationUpdate(BaseModel):
    final_status: str

class Application(ApplicationBase):
    id: int
    job_id: int
    candidate_id: int
    applied_on: datetime
    last_updated: datetime
    candidate: Candidate
    
    class Config:
        orm_mode = True

class CandidateApplication(Application):
    job: Job 