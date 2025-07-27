from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, db

router = APIRouter(
    prefix="/api/candidates",
    tags=["candidates"],
)

@router.get("/", response_model=List[schemas.Candidate])
def read_candidates(jobTitle: str = 'Aviator', sortBy: str = 'appliedOn', sortOrder: str = 'desc', db: Session = Depends(db.get_db)):
    # Basic validation
    if sortOrder.lower() not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="sortOrder must be 'asc' or 'desc'")
    
    query = db.query(db.Candidate).filter(db.Candidate.jobTitle == jobTitle)
    
    # Dynamic sorting
    if hasattr(db.Candidate, sortBy):
        column_to_sort = getattr(db.Candidate, sortBy)
        if sortOrder.lower() == 'asc':
            query = query.order_by(column_to_sort.asc())
        else:
            query = query.order_by(column_to_sort.desc())

    return query.all()


@router.patch("/{candidate_id}", response_model=schemas.Candidate)
def update_candidate_status(candidate_id: int, candidate_update: schemas.CandidateUpdate, db: Session = Depends(db.get_db)):
    db_candidate = db.query(db.Candidate).filter(db.Candidate.id == candidate_id).first()
    if db_candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    db_candidate.finalStatus = candidate_update.finalStatus
    db.commit()
    db.refresh(db_candidate)
    return db_candidate 