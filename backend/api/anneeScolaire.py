from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import models, db

router = APIRouter(prefix="/anneeScolaire", tags=["anneeScolaire"])

@router.get("/")
def list_annees(db: Session = Depends(db.get_db)):
    annees = db.query(models.AnneeScolaire).all()
    return annees