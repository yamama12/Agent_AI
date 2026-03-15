from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import models, db

router = APIRouter(prefix="/eleves", tags=["eleves"])

@router.get("/")
def list_eleves(db: Session = Depends(db.get_db)):
    eleves = db.query(models.Eleve).all()
    return eleves