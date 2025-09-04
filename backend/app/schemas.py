from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

#  Resume schema
class Resume(BaseModel):
    resume_hash: str
    resume_url: str
    is_invalid: bool = False

# Job Schemas
class JobBase(BaseModel):
    title: str
    description: str

class Job(JobBase):
    id: int
    created_at: datetime    
    class Config:
        orm_mode = True

# Candidate Schemas 
class CandidateBase(BaseModel):
    name: str
    email: str
    resume_hash: str    

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
    INVALID = "Invalid"

class FinalStatus(str, Enum):
    SHORTLISTED = LLMOutcome.SHORTLISTED.value
    REJECTED = LLMOutcome.REJECTED.value    
    FAILED = LLMOutcome.FAILED.value
    INVALID = LLMOutcome.INVALID.value
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
    file_url: str


class InvalidApplicationCreate(ApplicationBase):
    job_id: int
    candidate_id: int = -1 # invalid candidate

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
