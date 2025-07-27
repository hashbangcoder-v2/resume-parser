from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CandidateBase(BaseModel):
    name: str
    status: str
    reason: Optional[str] = None
    finalStatus: str
    jobTitle: str
    fileUrl: Optional[str] = None

class CandidateCreate(CandidateBase):
    pass

class CandidateUpdate(BaseModel):
    finalStatus: str

class Candidate(CandidateBase):
    id: int
    appliedOn: datetime

    class Config:
        orm_mode = True 