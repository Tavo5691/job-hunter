"""
Integration tests for the /api/v1/profiles router.
Uses TestClient + an in-memory SQLite database for isolation.
Mocks the PDF parser and LLM extractor to avoid real I/O.
"""

import uuid
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base, get_db
from app.main import app
from app.services.regex_extractor import ProfileExtraction, ProfileExtractorError

# ---------------------------------------------------------------------------
# Test database setup — use SQLite in-memory (no pgvector needed for unit tests)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_test_db():
    """Create all tables before each test, drop them after."""
    # Note: JSONB columns will fall back to JSON on SQLite
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_pdf_bytes() -> bytes:
    """Return some bytes that look like a PDF file."""
    return b"%PDF-1.4 fake content for testing purposes " * 10


def _make_extraction() -> ProfileExtraction:
    return ProfileExtraction(
        name="Jane Doe",
        email="jane@example.com",
        phone="+1-555-0100",
        summary="Experienced software engineer",
        skills=["Python", "FastAPI", "PostgreSQL"],
        work_experience=[],
        education=[],
        certifications=[],
        languages=[],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_health_check_from_profiles_module() -> None:
    """Sanity check — health endpoint works with test DB override."""
    resp = client.get("/health")
    assert resp.status_code == 200


def test_list_profiles_empty() -> None:
    resp = client.get("/api/v1/profiles")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_profile_happy_path() -> None:
    """POST /profiles should parse PDF, extract profile, persist and return it."""
    mock_text = "Jane Doe — Software Engineer with Python and FastAPI experience " * 5

    with (
        patch(
            "app.routers.profiles.extract_text_from_pdf",
            return_value=mock_text,
        ),
        patch(
            "app.routers.profiles.extract_profile_from_text",
            new=Mock(return_value=_make_extraction()),
        ),
    ):
        resp = client.post(
            "/api/v1/profiles",
            files={"file": ("cv.pdf", _fake_pdf_bytes(), "application/pdf")},
        )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane@example.com"
    assert "Python" in data["skills"]
    assert "id" in data
    assert "created_at" in data


def test_create_profile_rejects_non_pdf() -> None:
    """POST /profiles should return 422 for non-PDF files."""
    resp = client.post(
        "/api/v1/profiles",
        files={
            "file": (
                "resume.docx",
                b"fake docx content",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert resp.status_code == 422  # HTTP_422_UNPROCESSABLE_CONTENT


def test_create_profile_rejects_oversized_file() -> None:
    """POST /profiles should return 413 when file exceeds PDF_MAX_SIZE_MB."""
    # 11 MB of fake PDF content
    big_content = b"A" * (11 * 1024 * 1024)
    resp = client.post(
        "/api/v1/profiles",
        files={"file": ("large.pdf", big_content, "application/pdf")},
    )
    assert resp.status_code == 413  # HTTP_413_CONTENT_TOO_LARGE


def test_get_profile_not_found() -> None:
    """GET /profiles/{id} should return 404 for unknown ID."""
    unknown_id = str(uuid.uuid4())
    resp = client.get(f"/api/v1/profiles/{unknown_id}")
    assert resp.status_code == 404


def test_get_profile_after_create() -> None:
    """GET /profiles/{id} should return the created profile."""
    mock_text = "John Smith — Backend developer " * 10

    with (
        patch("app.routers.profiles.extract_text_from_pdf", return_value=mock_text),
        patch(
            "app.routers.profiles.extract_profile_from_text",
            new=Mock(
                return_value=ProfileExtraction(
                    name="John Smith",
                    skills=["Go", "Docker"],
                )
            ),
        ),
    ):
        create_resp = client.post(
            "/api/v1/profiles",
            files={"file": ("cv.pdf", _fake_pdf_bytes(), "application/pdf")},
        )

    profile_id = create_resp.json()["id"]
    get_resp = client.get(f"/api/v1/profiles/{profile_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "John Smith"


def test_delete_profile() -> None:
    """DELETE /profiles/{id} should remove the profile."""
    mock_text = "Alice — Frontend developer " * 10

    with (
        patch("app.routers.profiles.extract_text_from_pdf", return_value=mock_text),
        patch(
            "app.routers.profiles.extract_profile_from_text",
            new=Mock(return_value=ProfileExtraction(name="Alice")),
        ),
    ):
        create_resp = client.post(
            "/api/v1/profiles",
            files={"file": ("cv.pdf", _fake_pdf_bytes(), "application/pdf")},
        )

    profile_id = create_resp.json()["id"]
    del_resp = client.delete(f"/api/v1/profiles/{profile_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/profiles/{profile_id}")
    assert get_resp.status_code == 404


def test_update_profile() -> None:
    """PATCH /profiles/{id} should update specified fields and return the updated profile."""
    mock_text = "Bob Builder — Full-stack developer " * 10

    with (
        patch("app.routers.profiles.extract_text_from_pdf", return_value=mock_text),
        patch(
            "app.routers.profiles.extract_profile_from_text",
            new=Mock(
                return_value=ProfileExtraction(
                    name="Bob Builder",
                    email="bob@example.com",
                    summary="Original summary",
                    skills=["JavaScript", "React"],
                )
            ),
        ),
    ):
        create_resp = client.post(
            "/api/v1/profiles",
            files={"file": ("cv.pdf", _fake_pdf_bytes(), "application/pdf")},
        )

    assert create_resp.status_code == 201, create_resp.text
    original = create_resp.json()
    profile_id = original["id"]

    patch_resp = client.patch(
        f"/api/v1/profiles/{profile_id}",
        json={"name": "Robert Builder", "summary": "Updated summary"},
    )
    assert patch_resp.status_code == 200, patch_resp.text
    updated = patch_resp.json()

    # Updated fields reflect the new values
    assert updated["name"] == "Robert Builder"
    assert updated["summary"] == "Updated summary"

    # Unchanged fields remain the same
    assert updated["id"] == profile_id
    assert updated["created_at"] == original["created_at"]
    assert updated["email"] == "bob@example.com"
    assert "JavaScript" in updated["skills"]


def test_create_profile_extractor_error() -> None:
    """POST /profiles should return 502 when the LLM extractor raises ProfileExtractorError."""
    mock_text = "Some valid CV text " * 10

    with (
        patch("app.routers.profiles.extract_text_from_pdf", return_value=mock_text),
        patch(
            "app.routers.profiles.extract_profile_from_text",
            new=Mock(side_effect=ProfileExtractorError("OpenAI API error: timeout")),
        ),
    ):
        resp = client.post(
            "/api/v1/profiles",
            files={"file": ("cv.pdf", _fake_pdf_bytes(), "application/pdf")},
        )

    assert resp.status_code == 502, resp.text
    assert "extraction failed" in resp.json()["detail"].lower()
