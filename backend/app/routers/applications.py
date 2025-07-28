from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.db import get_db

router = APIRouter(
    prefix="/api/applications",
    tags=["applications"],
)

@router.patch("/{application_id}", response_model=schemas.Application)
def update_application_status(application_id: int, status: schemas.ApplicationUpdate, db: Session = Depends(get_db)):
    db_application = crud.update_application_status(db, application_id=application_id, status=status)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return db_application 