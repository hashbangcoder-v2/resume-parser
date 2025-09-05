from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any
from enum import Enum

# Logged in User schema
class LoggedInUser(BaseModel):
    id: int
    name: str
    email: str

#  Resume schema
class Resume(BaseModel):
    hash: str
    resume_uri: str
    is_invalid: bool = False
    images: List[Any] = Field(default_factory=list)  # Use Any for PIL Images
    
    class Config:
        arbitrary_types_allowed = True  # Allow PIL Image objects

# Job Schemas
class JobBase(BaseModel):
    title: str
    description: str

class Job(JobBase):
    id: int
    created_at: datetime    
    class Config:
        from_attributes = True

# Candidate Schemas 
class Candidate(BaseModel):
    name: str
    email: str
    resume_hash: str  
    id: int = None

    class Config:
        from_attributes = True

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
    file_uri: str

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
        from_attributes = True


# PRocessOutcome schema
class Outcome(Enum):
    SUCCESS = "Success" # Successfully processed the resume
    SKIPPED = "Skipped" # Skipped the resume because it already exists
    LLM_ERROR = "LLM Error"
    SERVER_ERROR = "Server Error"

class ProcessOutcome(BaseModel):
    outcome: Outcome
    message: str = None