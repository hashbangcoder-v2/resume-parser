from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "sqlite:///./candidates.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    status = Column(String)
    appliedOn = Column(DateTime, default=datetime.datetime.utcnow)
    reason = Column(String)
    finalStatus = Column(String)
    jobTitle = Column(String)
    fileUrl = Column(String)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 