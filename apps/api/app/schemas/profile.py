"""
Pydantic schemas for the Profile resource.

Design note: schema mirrors the Profile ORM model but uses pure Python types.
WorkExperience, Education, etc. are nested models to support structured LLM output.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# ---------------------------------------------------------------------------
# Nested schemas
# ---------------------------------------------------------------------------


class WorkExperience(BaseModel):
    company: str
    title: str
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class Certification(BaseModel):
    name: str
    issuer: str | None = None
    date: str | None = None


class Language(BaseModel):
    language: str
    proficiency: str | None = None


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ProfileBase(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    summary: str | None = None
    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)


class ProfileCreate(ProfileBase):
    """Used internally when saving an extracted profile."""

    source_filename: str
    raw_text: str


class ProfileUpdate(ProfileBase):
    """Used for PATCH requests — all fields optional (inherited from ProfileBase)."""

    pass


class ProfileResponse(ProfileBase):
    """Full profile returned by GET and POST /profiles."""

    id: uuid.UUID
    source_filename: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
