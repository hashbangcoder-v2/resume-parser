from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    applications = relationship("Application", back_populates="job")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    resume_hash = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    applications = relationship("Application", back_populates="candidate")    

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    applied_on = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String)
    final_status = Column(String)
    reason = Column(String)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    file_url = Column(String)
    resume_hash = Column(String, unique=True, nullable=False)
    is_invalid = Column(Boolean, default=False)
    
    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
