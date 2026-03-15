from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import models, db

router = APIRouter(prefix="/localites", tags=["localites"])
@router.get("/")
def list_localites(db: Session = Depends(db.get_db)):
    localites = db.query(models.Localite).all()
    return localites
