from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import models, db

router = APIRouter(prefix="/inscriptionsEleves", tags=["inscriptionsEleves"])

@router.get("/")
def list_inscriptions_eleves(db: Session = Depends(db.get_db)):
    inscriptions = db.query(models.InscriptionEleve).all()
    return inscriptions