from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import models, db

router = APIRouter(prefix="/classes", tags=["classes"])

@router.get("/")
def list_classes(db: Session = Depends(db.get_db)):
    classes = db.query(models.Classe).all()
    return classes