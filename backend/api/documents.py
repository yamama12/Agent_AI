from services.docx_service import generate_CertificatScolarite_docx
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from database.eleve_repository import get_eleve_data
from services.pdf_service import generate_attestationInscri_pdf, generate_attestationPresence_pdf

router = APIRouter()

@router.get("/attestation_inscription/{matricule}")
def get_attestation(matricule: str):
    try:
        data = get_eleve_data(matricule)
    except Exception:
        raise HTTPException(status_code=404, detail="Élève non trouvé")

    file_path = f"files/attestation_{matricule}.pdf"
    generate_attestationInscri_pdf(data, file_path)

    return FileResponse(
        file_path, 
        media_type="application/pdf",
        filename=f"attestation_{matricule}.pdf"
        )

@router.get("/attestation_presence/{matricule}")
def get_attestation_presence(matricule: str):
    try:
        data = get_eleve_data(matricule)
    except Exception:
        raise HTTPException(status_code=404, detail="Élève non trouvé")

    file_path = f"files/attestation_presence_{matricule}.pdf"
    generate_attestationPresence_pdf(data, file_path)

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"attestation_presence_{matricule}.pdf"
    )

@router.get("/certificat/{matricule}")
def get_certificat(matricule: str):
    try:
        data = get_eleve_data(matricule)
    except Exception:
        raise HTTPException(status_code=404, detail="Élève non trouvé")

    file_path = f"files/certificat_{matricule}.docx"
    generate_CertificatScolarite_docx(data, file_path)

    return FileResponse(
        file_path, 
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"certificat_{matricule}.docx"
        )


