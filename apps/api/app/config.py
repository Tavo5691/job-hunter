"""
Application configuration — reads from environment variables / .env file.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql://job_hunter:secret@localhost:5432/job_hunter_db"

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Extractor toggle (set USE_LLM_EXTRACTOR=true to use OpenAI-based extraction)
    USE_LLM_EXTRACTOR: bool = False

    # PDF upload limits
    PDF_MAX_SIZE_MB: int = 10

    # App metadata
    APP_NAME: str = "job-hunter API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    @field_validator("PDF_MAX_SIZE_MB")
    @classmethod
    def validate_pdf_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("PDF_MAX_SIZE_MB must be positive")
        return v

    @property
    def pdf_max_size_bytes(self) -> int:
        return self.PDF_MAX_SIZE_MB * 1024 * 1024

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
