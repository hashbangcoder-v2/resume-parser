from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from app.config import get_config
from app import db_models
from app.logger import logger


DATABASE_URL = get_config().database.url
DATABASE_DIR = Path(get_config().database.directory)

if not Path(DATABASE_DIR).exists():
    logger.warning(f"Database directory does not exist: {DATABASE_DIR}. Creating it...")
    Path(DATABASE_DIR).mkdir(parents=True, exist_ok=True)

DATABASE_FILE = DATABASE_DIR / Path(DATABASE_URL).name

if not DATABASE_FILE.exists() and get_config().database.create_if_not_exists:
    DATABASE_FILE.touch()
    logger.info(f"Database file created: {DATABASE_FILE}")

engine = create_engine(str(DATABASE_URL), connect_args={"check_same_thread": False})
db_models.Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
        logger.info(f"Database connection opened: {DATABASE_URL}")
    finally:
        db.close() 