"""
Regex-based profile extraction service.

This module provides a fallback profile extractor using pattern matching
when LLM extraction is not available or disabled.
"""

import re

from pydantic import BaseModel, Field

from app.schemas.profile import (
    Certification,
    Education,
    Language,
    WorkExperience,
)


class ProfileExtraction(BaseModel):
    """Structured profile data extracted from CV text by regex patterns."""

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    summary: str | None = None
    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)


class ProfileExtractorError(Exception):
    """Raised when regex extraction fails or returns invalid data."""


KNOWN_SKILLS = {
    "Python",
    "FastAPI",
    "Django",
    "Flask",
    "React",
    "Vue",
    "Angular",
    "Svelte",
    "Next.js",
    "Nuxt",
    "TypeScript",
    "JavaScript",
    "Java",
    "Spring",
    "Spring Boot",
    "C#",
    ".NET",
    "ASP.NET",
    "Go",
    "Golang",
    "Rust",
    "C++",
    "C",
    "Ruby",
    "Ruby on Rails",
    "PHP",
    "Laravel",
    "Swift",
    "Kotlin",
    "Scala",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "SQLite",
    "Elasticsearch",
    "Docker",
    "Kubernetes",
    "Helm",
    "AWS",
    "Azure",
    "GCP",
    "Google Cloud",
    "Terraform",
    "Ansible",
    "Jenkins",
    "GitLab CI",
    "GitHub Actions",
    "CircleCI",
    "Linux",
    "Bash",
    "Shell",
    "GraphQL",
    "REST",
    "gRPC",
    "RabbitMQ",
    "Kafka",
    "Nginx",
    "Apache",
    "CI/CD",
    "DevOps",
    "Machine Learning",
    "TensorFlow",
    "PyTorch",
    "Pandas",
    "NumPy",
}


def extract_profile_from_text(raw_text: str) -> ProfileExtraction:
    """
    Extract structured profile from raw CV text using regex patterns.

    Args:
        raw_text: plain text extracted from a PDF CV

    Returns:
        ProfileExtraction with all available fields populated

    Raises:
        ProfileExtractorError: if extraction fails
    """
    profile = ProfileExtraction()

    profile.email = _extract_email(raw_text)
    profile.phone = _extract_phone(raw_text)
    profile.name = _extract_name(raw_text)
    profile.skills = _extract_skills(raw_text)
    profile.summary = _extract_summary(raw_text)
    profile.work_experience = _extract_work_experience(raw_text)
    profile.education = _extract_education(raw_text)
    profile.certifications = _extract_certifications(raw_text)
    profile.languages = _extract_languages(raw_text)

    return profile


def _extract_email(text: str) -> str | None:
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    match = re.search(pattern, text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> str | None:
    patterns = [
        r"\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}",
        r"\+?[0-9]{1,4}[-.\s]?[0-9]{2,4}[-.\s]?[0-9]{2,4}[-.\s]?[0-9]{2,4}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def _extract_name(text: str) -> str | None:
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    phone_pattern = r"\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"

    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if len(line) > 60:
            continue
        if re.search(email_pattern, line):
            continue
        if re.search(phone_pattern, line):
            continue
        return line
    return None


def _extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found_skills = []
    for skill in KNOWN_SKILLS:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    return list(set(found_skills))


def _extract_section(text: str, headers: list[str]) -> str:
    """Find text between a matched section header and the next section header."""
    headers_pattern = "|".join(re.escape(h) for h in headers)
    pattern = rf"(?:{headers_pattern})[:\s]*(.*?)(?:{headers_pattern}|$)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_summary(text: str) -> str | None:
    section = _extract_section(text, ["summary", "objective", "profile", "about"])
    if section:
        return section[:500]
    return None


def _extract_work_experience(text: str) -> list[WorkExperience]:
    experiences = []
    exp_section = re.search(
        r"(?:experience|employment|work history)[:\s]*(.*?)(?:education|skills|certifications|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not exp_section:
        return experiences

    exp_text = exp_section.group(1)
    entries = re.split(r"(?:^|\n)(?=[A-Z][^a-z]|$)", exp_text)

    for entry in entries[:10]:
        entry = entry.strip()
        if len(entry) < 20:
            continue

        company_match = re.search(
            r"^(?:(?:\d{4}[-/]\d{4})|(?:\d{4}\s*-\s*(?:\d{4}|present)))\s*[-:]?\s*([^\n]+)",
            entry,
            re.MULTILINE,
        )
        company = company_match.group(1).strip() if company_match else "Unknown Company"

        title_match = re.search(r"(?:^|\n)([^\n]+)", entry)
        title = title_match.group(1).strip() if title_match else "Unknown Title"

        date_match = re.search(r"(\d{4}[-/]\d{4}|\d{4}\s*-\s*(?:\d{4}|present))", entry)
        start_date = date_match.group(1) if date_match else None

        tech_match = re.findall(
            r"(?:technologies?|tools?|tech)[:\s]*([^\n]+)", entry, re.IGNORECASE
        )
        technologies = []
        if tech_match:
            for tech in KNOWN_SKILLS:
                if tech.lower() in tech_match[0].lower():
                    technologies.append(tech)

        experiences.append(
            WorkExperience(
                company=company,
                title=title,
                start_date=start_date,
                description=entry[:300] if len(entry) > 300 else entry,
                technologies=technologies,
            )
        )

    return experiences


def _extract_education(text: str) -> list[Education]:
    education_list = []
    edu_section = re.search(
        r"(?:education|academic)[:\s]*(.*?)(?:experience|skills|certifications|employment|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not edu_section:
        return education_list

    edu_text = edu_section.group(1)
    entries = re.split(r"(?:^|\n)(?=[A-Z])", edu_text)

    for entry in entries[:5]:
        entry = entry.strip()
        if len(entry) < 10:
            continue

        institution_match = re.search(
            r"^(?:(?:\d{4}[-/]\d{4})|(?:\d{4}\s*-\s*(?:\d{4}|present)))\s*[-:]?\s*([^\n]+)",
            entry,
            re.MULTILINE,
        )
        institution = (
            institution_match.group(1).strip() if institution_match else "Unknown Institution"
        )

        degree_match = re.search(
            r"(?:bachelor|master|phd|doctorate|degree)[:\s]*(?:in\s*)?([^\n,]+)",
            entry,
            re.IGNORECASE,
        )
        degree = degree_match.group(1).strip() if degree_match else None

        field_match = re.search(r"(?:in|of)\s+([A-Za-z\s]+?)(?:\s*[,/]|\s*$)", entry)
        field_of_study = field_match.group(1).strip() if field_match else None

        date_match = re.search(r"(\d{4}[-/]\d{4}|\d{4}\s*-\s*(?:\d{4}|present|ongoing))", entry)
        start_date = date_match.group(1) if date_match else None

        education_list.append(
            Education(
                institution=institution,
                degree=degree,
                field_of_study=field_of_study,
                start_date=start_date,
            )
        )

    return education_list


def _extract_certifications(text: str) -> list[Certification]:
    certifications = []
    cert_section = re.search(
        r"(?:certifications?|certificates?|licenses?)[:\s]*(.*?)(?:experience|education|skills|languages|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not cert_section:
        return certifications

    cert_text = cert_section.group(1)
    entries = re.split(r"[•\n]", cert_text)

    for entry in entries:
        entry = entry.strip()
        if len(entry) < 3:
            continue

        name = entry.strip()

        issuer_match = re.search(
            r"(?:from|by|issued\s+(?:by|from))\s+([A-Za-z\s]+?)(?:\s*[,/]|\s*$)",
            entry,
            re.IGNORECASE,
        )
        issuer = issuer_match.group(1).strip() if issuer_match else None

        date_match = re.search(r"(\d{4}|\d{4}[-/]\d{2})", entry)
        date = date_match.group(1) if date_match else None

        certifications.append(
            Certification(
                name=name,
                issuer=issuer,
                date=date,
            )
        )

    return certifications


def _extract_languages(text: str) -> list[Language]:
    languages = []
    lang_section = re.search(
        r"(?:languages?|spoken\s*languages?)[:\s]*(.*?)(?:experience|education|skills|certifications|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not lang_section:
        return languages

    lang_text = lang_section.group(1)
    entries = re.split(r"[,\n•]", lang_text)

    common_proficiencies = ["native", "fluent", "professional", "intermediate", "basic", "beginner"]

    for entry in entries:
        entry = entry.strip()
        if len(entry) < 2 or len(entry) > 30:
            continue

        proficiency = None
        language = entry
        entry_lower = entry.lower()

        for prof in common_proficiencies:
            if prof in entry_lower:
                proficiency = prof.capitalize()
                language = re.sub(prof, "", entry_lower).strip().title()
                break

        if not proficiency:
            language = entry.title()

        languages.append(
            Language(
                language=language,
                proficiency=proficiency,
            )
        )

    return languages
