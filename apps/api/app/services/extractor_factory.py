"""
Extractor factory service.

Provides the appropriate profile extractor based on USE_LLM_EXTRACTOR env var.
"""

from app.config import settings


def get_extractor():
    """
    Returns the appropriate profile extractor based on USE_LLM_EXTRACTOR setting.

    If USE_LLM_EXTRACTOR=true and OPENAI_API_KEY is set, returns the async LLM extractor.
    Otherwise, returns the synchronous regex-based extractor.
    """
    if settings.USE_LLM_EXTRACTOR and settings.OPENAI_API_KEY:
        from app.services.llm_extractor import create_llm_extractor

        return create_llm_extractor()
    return None


def is_llm_extractor_enabled() -> bool:
    """Check if LLM extractor is enabled."""
    return settings.USE_LLM_EXTRACTOR and bool(settings.OPENAI_API_KEY)
