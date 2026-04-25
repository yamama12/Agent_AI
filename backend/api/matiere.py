from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import models, db

router = APIRouter(prefix="/matieres", tags=["matieres"])

@router.get("/")
def list_matieres(db: Session = Depends(db.get_db)):
    matieres = db.query(models.Matiere).all()
    return matieres