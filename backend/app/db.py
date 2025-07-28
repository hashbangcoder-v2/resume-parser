from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import get_config
from .models import Base
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = get_config().database.url
logger.info(f"Database connection opened: {DATABASE_URL}")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
        logger.info(f"Database connection opened: {DATABASE_URL}")
    finally:
        db.close() 