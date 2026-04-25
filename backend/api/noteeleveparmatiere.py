from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import models, db

router = APIRouter(prefix="/notes", tags=["notes"])

@router.get("/")
def list_notes(db: Session = Depends(db.get_db)):
    notes = db.query(models.Note).all()
    return notes