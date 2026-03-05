"""
LLM-based profile extraction service.

This module provides an OpenAI-based profile extractor when USE_LLM_EXTRACTOR=true.
"""

from typing import Any

from openai import AsyncOpenAI

from app.schemas.profile import (
    Certification,
    Education,
    Language,
    WorkExperience,
)
from app.services.regex_extractor import ProfileExtraction


class LLMExtractorError(Exception):
    """Raised when LLM extraction fails."""


def create_llm_extractor():
    """Create an async LLM extractor function with OpenAI."""
    client = AsyncOpenAI()

    async def extract_profile_from_text(raw_text: str) -> ProfileExtraction:
        """
        Extract structured profile from raw CV text using OpenAI.

        Args:
            raw_text: plain text extracted from a PDF CV

        Returns:
            ProfileExtraction with all available fields populated

        Raises:
            LLMExtractorError: if extraction fails
        """
        prompt = f"""Extract the following CV text into a structured JSON profile with these fields:
- name: Full name
- email: Email address
- phone: Phone number
- summary: Professional summary/objective (2-3 sentences)
- work_experience: Array of {{company, title, start_date, end_date, description, technologies}}
- education: Array of {{institution, degree, field_of_study, start_date, end_date}}
- skills: Array of technical skills
- certifications: Array of {{name, issuer, date}}
- languages: Array of {{language, proficiency}}

CV Text:
{raw_text[:3000]}

Return ONLY valid JSON, no other text."""

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a CV parser. Extract structured data from CV text.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            content = response.choices[0].message.content
            if not content:
                raise LLMExtractorError("Empty response from OpenAI")

            import json

            data: dict[str, Any] = json.loads(content)

            return ProfileExtraction(
                name=data.get("name"),
                email=data.get("email"),
                phone=data.get("phone"),
                summary=data.get("summary"),
                work_experience=[WorkExperience(**w) for w in data.get("work_experience", [])],
                education=[Education(**e) for e in data.get("education", [])],
                skills=data.get("skills", []),
                certifications=[Certification(**c) for c in data.get("certifications", [])],
                languages=[Language(**lang) for lang in data.get("languages", [])],
            )
        except Exception as exc:
            raise LLMExtractorError(f"OpenAI extraction failed: {exc}") from exc

    return extract_profile_from_text
