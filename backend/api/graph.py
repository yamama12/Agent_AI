from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from services.graph_service import (
    generate_students_by_class_chart,
    generate_students_by_gender_chart,
    generate_students_by_locality_chart,
)

router = APIRouter(prefix="/graphs", tags=["Graphes"])


@router.get(
    "/students-by-class",
    summary="Graphe - Nombre d'eleves par classe",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Graphe genere automatiquement",
        }
    },
)
def students_by_class():
    image = generate_students_by_class_chart()
    return StreamingResponse(image, media_type="image/png")


@router.get(
    "/students-by-gender",
    summary="Graphe - Repartition des eleves par sexe",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Graphe genere automatiquement",
        }
    },
)
def students_by_gender():
    image = generate_students_by_gender_chart()
    return StreamingResponse(image, media_type="image/png")


@router.get(
    "/students-by-locality",
    summary="Graphe - Repartition des eleves par localite",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Graphe genere automatiquement",
        }
    },
)
def students_by_locality():
    image = generate_students_by_locality_chart()
    return StreamingResponse(image, media_type="image/png")

