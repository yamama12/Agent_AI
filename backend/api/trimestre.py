from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import models, db

router = APIRouter(prefix="/trimestres", tags=["trimestres"])

@router.get("/")
def list_trimestres(db: Session = Depends(db.get_db)):
    trimestres = db.query(models.Eleve).all()
    return trimestres