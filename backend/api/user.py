import json
import os
from typing import List, Optional, Union
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DataError
from passlib.context import CryptContext
from database import models, db

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on"}
    return False


def _integrity_error_detail(exc: IntegrityError) -> str:
    message = str(getattr(exc, "orig", exc)).lower()
    if "tel1" in message:
        return "Telephone deja utilise"
    if "index_cin" in message or "cin" in message:
        return "CIN deja utilise"
    if "email" in message:
        return "Identifiant deja utilise"
    return "Contrainte de base de donnees invalide"


def _normalize_optional_string(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _parse_roles(roles: Optional[Union[List[str], str]]) -> Optional[List[str]]:
    if roles is None:
        return None
    if isinstance(roles, list):
        return [str(role) for role in roles]
    if isinstance(roles, str):
        try:
            parsed = json.loads(roles)
            if isinstance(parsed, list):
                return [str(role) for role in parsed]
            if parsed:
                return [str(parsed)]
        except json.JSONDecodeError:
            if roles.strip():
                return [roles.strip()]
    return []


def _serialize_user(user: models.User, person: Optional[models.Personne]) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "idpersonne": user.idpersonne,
        "roles": user.roles,
        "token": user.token,
        "changepassword": _as_bool(user.changepassword),
        "nom": person.NomFr if person else None,
        "prenom": person.PrenomFr if person else None,
        "telephone": person.Tel1 if person else None,
        "cin": person.Cin if person else None,
        "email_personne": person.Email if person else None,
    }

@router.get("/admins")
def list_personnes(db: Session = Depends(db.get_db)):

    users = (
        db.query(models.User, models.Personne)
        .outerjoin(models.Personne, models.User.idpersonne == models.Personne.id)
        .filter(
            (models.User.roles.contains("ROLE_ADMIN")) |
            (models.User.roles.contains("ROLE_SUPER_ADMIN"))
        )
        .all()
    )

    results = []
    for user, personne in users:
        results.append({
            "id": user.id,
            "email": user.email,
            "idpersonne": user.idpersonne,
            "roles": user.roles,
            "token": user.token,
            "changepassword": _as_bool(user.changepassword),
            "nom": personne.NomFr if personne else None,
            "prenom": personne.PrenomFr if personne else None,
            "telephone": personne.Tel1 if personne else None,
            "cin": personne.Cin if personne else None,
            "email_personne": personne.Email if personne else None,
        })

    return results


class UserCreate(BaseModel):
    nom: str
    prenom: str
    telephone: str
    cin: str
    email: Optional[str] = None
    email_personne: Optional[str] = None
    password: str
    roles: Union[List[str], str]
    changepassword: Optional[bool] = False


class UserUpdate(BaseModel):
    telephone: Optional[str] = None
    email_personne: Optional[str] = None
    password: Optional[str] = None
    roles: Optional[Union[List[str], str]] = None
    changepassword: Optional[bool] = None

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(db.get_db)):

    # Verifier si l'identifiant de connexion est deja utilise
    telephone = user.telephone.strip()
    cin = user.cin.strip()
    login_email = (user.email or "").strip()
    if not login_email:
        login_email = telephone

    if not login_email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="email ou telephone requis",
        )

    if login_email != telephone:
        raise HTTPException(
            status_code=400,
            detail="L'identifiant doit être le numéro de téléphone ",
        )

    existing_user = db.query(models.User).filter(
        models.User.email == login_email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Identifiant deja utilise")

    # Creer ou reutiliser Personne
    person_email = _normalize_optional_string(user.email_personne)
    existing_person_query = []
    if telephone:
        existing_person_query.append(models.Personne.Tel1 == telephone)
    if cin:
        existing_person_query.append(models.Personne.Cin == cin)
    if person_email:
        existing_person_query.append(models.Personne.Email == person_email)

    matches = []
    if existing_person_query:
        matches = db.query(models.Personne).filter(or_(*existing_person_query)).all()

    if len(matches) > 1:
        raise HTTPException(
            status_code=400,
            detail="Plusieurs personnes correspondent. Precisez l'identite.",
        )

    existing_person = matches[0] if len(matches) == 1 else None
    if existing_person:
        conflicts = []
        if existing_person.Tel1 and existing_person.Tel1 != telephone:
            conflicts.append("telephone")
        if existing_person.Cin and existing_person.Cin != cin:
            conflicts.append("cin")
        if person_email and existing_person.Email and existing_person.Email != person_email:
            conflicts.append("email")
        if conflicts:
            raise HTTPException(
                status_code=400,
                detail=f"Donnees personne incoherentes: {', '.join(conflicts)}",
            )

        existing_user_for_person = db.query(models.User).filter(
            models.User.idpersonne == existing_person.id
        ).first()
        if existing_user_for_person:
            raise HTTPException(
                status_code=400,
                detail="Utilisateur deja associe a cette personne",
            )

        updated = False
        if not existing_person.Tel1 and telephone:
            existing_person.Tel1 = telephone
            updated = True
        if not existing_person.Cin and cin:
            existing_person.Cin = cin
            updated = True
        if not existing_person.Email and person_email:
            existing_person.Email = person_email
            updated = True
        if updated:
            db.add(existing_person)

        person = existing_person
    else:
        person = models.Personne(
            NomFr = user.nom,
            PrenomFr = user.prenom,
            Tel1 = telephone,
            Cin = cin,
            Email = person_email,
        )

    # Creer User
    roles_list = _parse_roles(user.roles) or []
    roles_json = json.dumps(roles_list)

    try:
        if existing_person is None:
            db.add(person)
            db.flush()
        new_user = models.User(
            email = login_email,
            password = hash_password(user.password),
            idpersonne = person.id,
            roles = roles_json,
            token = None,
            changepassword = _as_bool(user.changepassword),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=_integrity_error_detail(exc)) from exc
    except DataError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Valeurs invalides") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        detail = "Erreur base de donnees"
        if os.getenv("DEBUG_SQL_ERRORS", "").lower() == "true":
            detail = f"Erreur base de donnees: {exc}"
        raise HTTPException(status_code=500, detail=detail) from exc

    return _serialize_user(new_user, person)


@router.put("/{user_id}", status_code=status.HTTP_200_OK)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(db.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )

    person = db.query(models.Personne).filter(models.Personne.id == user.idpersonne).first()
    if person is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personne associee introuvable",
        )

    telephone = payload.telephone.strip() if payload.telephone is not None else (person.Tel1 or user.email or "").strip()
    email_personne = _normalize_optional_string(payload.email_personne)
    roles_list = _parse_roles(payload.roles)
    new_password = payload.password.strip() if payload.password is not None else None

    if not telephone:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Telephone requis",
        )

    if payload.password is not None:
        if not new_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Mot de passe requis",
            )
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le mot de passe doit contenir au moins 6 caracteres",
            )

    existing_user = db.query(models.User).filter(
        models.User.email == telephone,
        models.User.id != user.id,
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Identifiant deja utilise")

    existing_person = db.query(models.Personne).filter(
        models.Personne.Tel1 == telephone,
        models.Personne.id != person.id,
    ).first()
    if existing_person:
        raise HTTPException(status_code=400, detail="Telephone deja utilise")

    user.email = telephone
    person.Tel1 = telephone

    if payload.email_personne is not None:
        person.Email = email_personne

    if roles_list is not None:
        user.roles = json.dumps(roles_list)

    if payload.changepassword is not None:
        user.changepassword = _as_bool(payload.changepassword)

    if new_password is not None:
        user.password = hash_password(new_password)

    try:
        db.add(person)
        db.add(user)
        db.commit()
        db.refresh(user)
        db.refresh(person)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=_integrity_error_detail(exc)) from exc
    except DataError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Valeurs invalides") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        detail = "Erreur lors de la modification de l'utilisateur"
        if os.getenv("DEBUG_SQL_ERRORS", "").lower() == "true":
            detail = f"Erreur lors de la modification de l'utilisateur: {exc}"
        raise HTTPException(status_code=500, detail=detail) from exc

    return _serialize_user(user, person)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: int, db: Session = Depends(db.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )

    try:
        deleted_user = {
            "id": user.id,
            "email": user.email,
            "idpersonne": user.idpersonne,
        }
        db.delete(user)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        detail = "Erreur lors de la suppression de l'utilisateur"
        if os.getenv("DEBUG_SQL_ERRORS", "").lower() == "true":
            detail = f"Erreur lors de la suppression de l'utilisateur: {exc}"
        raise HTTPException(status_code=500, detail=detail) from exc

    return {
        "message": "Utilisateur supprimé avec succés",
        "user": deleted_user,
    }
