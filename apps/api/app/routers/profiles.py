"""
Profiles router.

Endpoints:
  POST   /profiles        — Upload a PDF, extract profile, store and return it
  GET    /profiles        — List all profiles (id + name + created_at)
  GET    /profiles/{id}   — Get a single profile by ID
  PATCH  /profiles/{id}   — Update a profile (user edits)
  DELETE /profiles/{id}   — Delete a profile

Design: POST /profiles is fully synchronous (see design decision: synchronous extraction).
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.extractor_factory import get_extractor
from app.services.pdf_parser import PDFParserError, extract_text_from_pdf
from app.services.regex_extractor import ProfileExtractorError, extract_profile_from_text

router = APIRouter(prefix="/profiles", tags=["profiles"])

DbSession = Annotated[Session, Depends(get_db)]
PdfUpload = Annotated[UploadFile, File(description="PDF file containing the developer's CV")]


@router.post(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF CV and extract a developer profile",
)
async def create_profile(
    db: DbSession,
    file: PdfUpload,
) -> Profile:
    """
    Upload a PDF CV, parse its text, run LLM extraction, persist and return the profile.

    - Validates file type (must be application/pdf or .pdf extension)
    - Validates file size (≤ PDF_MAX_SIZE_MB)
    - Extracts text via PyMuPDF (with pdfminer fallback)
    - Calls OpenAI to structure the profile
    - Stores the result in PostgreSQL
    - Returns the full structured profile
    """
    # Validate content type
    if not _is_pdf(file):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Only PDF files are accepted.",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > settings.pdf_max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.PDF_MAX_SIZE_MB} MB.",
        )

    # Extract text
    try:
        raw_text = extract_text_from_pdf(content)
    except PDFParserError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Could not extract text from PDF: {exc}",
        ) from exc

    # Extract structured profile
    extractor_fn = get_extractor()
    try:
        if extractor_fn:
            extracted = await extractor_fn(raw_text)
        else:
            extracted = extract_profile_from_text(raw_text)
    except ProfileExtractorError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Profile extraction failed: {exc}",
        ) from exc

    # Persist
    profile = Profile(
        source_filename=file.filename or "unknown.pdf",
        raw_text=raw_text,
        name=extracted.name,
        email=extracted.email,
        phone=extracted.phone,
        summary=extracted.summary,
        work_experience=[e.model_dump() for e in extracted.work_experience],
        education=[e.model_dump() for e in extracted.education],
        skills=extracted.skills,
        certifications=[c.model_dump() for c in extracted.certifications],
        languages=[lang.model_dump() for lang in extracted.languages],
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get(
    "",
    response_model=list[ProfileResponse],
    summary="List all profiles",
)
def list_profiles(db: DbSession) -> list[Profile]:
    return db.query(Profile).order_by(Profile.created_at.desc()).all()


@router.get(
    "/{profile_id}",
    response_model=ProfileResponse,
    summary="Get a profile by ID",
)
def get_profile(profile_id: uuid.UUID, db: DbSession) -> Profile:
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch(
    "/{profile_id}",
    response_model=ProfileResponse,
    summary="Update a profile",
)
def update_profile(
    profile_id: uuid.UUID,
    updates: ProfileUpdate,
    db: DbSession,
) -> Profile:
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    update_data = updates.model_dump(exclude_unset=True)
    # Serialize nested models to plain dicts/lists before persisting
    list_fields = {"work_experience", "education", "certifications", "languages"}
    for field, value in update_data.items():
        if field in list_fields and value is not None:
            value = [item.model_dump() if hasattr(item, "model_dump") else item for item in value]
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a profile",
)
def delete_profile(profile_id: uuid.UUID, db: DbSession) -> None:
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(profile)
    db.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_pdf(file: UploadFile) -> bool:
    """Return True if the upload looks like a PDF (by content-type or filename)."""
    if file.content_type == "application/pdf":
        return True
    if file.filename and file.filename.lower().endswith(".pdf"):
        return True
    return False
