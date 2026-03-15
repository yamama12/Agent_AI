from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import models, db

router = APIRouter(prefix="/civilites", tags=["civilites"])

@router.get("/")
def list_civilites(db: Session = Depends(db.get_db)):
    civilites = db.query(models.Civilite).all()
    return civilites