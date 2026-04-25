from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from services.graph_service import (
    generate_students_by_class_chart,
    generate_students_by_gender_chart,
    generate_students_by_locality_chart,
    generate_average_grades_by_class_chart,
    generate_grades_distribution_chart,
    generate_top_students_chart,
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

@router.get(
    "/average_grades_by_class",
    summary="Graphe - Repartition des notes moyennes par classe",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Graphe genere automatiquement",
        }
    },
)
def average_grades_by_class():
    image = generate_average_grades_by_class_chart()
    return StreamingResponse(image, media_type="image/png")


""" @router.get(
    "/average_grades_by_subject",
    summary="Graphe - Repartition des notes moyennes par matière",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Graphe genere automatiquement",
        }
    },
)
def average_grades_by_subject():
    image = generate_average_grades_by_subject_chart()
    return StreamingResponse(image, media_type="image/png") """

@router.get(
    "/grades_distribution",
    summary="Graphe - Repartition des notes",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Graphe genere automatiquement",
        }
    },
)
def grades_distribution():
    image = generate_grades_distribution_chart()
    return StreamingResponse(image, media_type="image/png")

@router.get(
    "/top_students",
    summary="Graphe - Meilleurs eleves",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Graphe genere automatiquement",
        }
    },
)
def top_students():
    image = generate_top_students_chart()
    return StreamingResponse(image, media_type="image/png")