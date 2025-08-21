from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

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

# LLM Schemas
class LLMOutcome(str, Enum):
    SHORTLISTED = "Shortlisted"
    REJECTED = "Rejected"
    NEEDS_REVIEW = "Needs Review"
    FAILED = "Failed"

# Human overrides if any
class FinalStatus(str, Enum):
    SHORTLISTED = LLMOutcome.SHORTLISTED.value
    REJECTED = LLMOutcome.REJECTED.value
    NEEDS_REVIEW = LLMOutcome.NEEDS_REVIEW.value
    FAILED = LLMOutcome.FAILED.value
    TBD = '-'

class LLMResponse(BaseModel):
    name: str
    email: str
    outcome: LLMOutcome
    reason: str

# Application Schemas
class ApplicationBase(BaseModel):
    status: str    
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