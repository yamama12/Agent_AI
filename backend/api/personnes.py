from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import models, db

router = APIRouter(prefix="/personnes", tags=["personnes"])

@router.get("/")
def list_personnes(db: Session = Depends(db.get_db)):
    personnes = db.query(models.Personne).all()
    return personnes

