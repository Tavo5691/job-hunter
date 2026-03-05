"""
PDF text extraction service.

Design decision: try PyMuPDF first; fall back to pdfminer.six if extracted text
is empty or raises an error. This handles both vector and scanned PDFs.
"""
import io
import logging

logger = logging.getLogger(__name__)

_MIN_TEXT_LENGTH = 50  # bytes; below this we consider extraction failed


class PDFParserError(Exception):
    """Raised when text cannot be extracted from the PDF."""


def extract_text_from_pdf(content: bytes) -> str:
    """
    Extract all text from a PDF file given as raw bytes.

    Args:
        content: raw bytes of the PDF file

    Returns:
        Extracted text string (may contain whitespace-only lines)

    Raises:
        PDFParserError: if neither parser can extract meaningful text
    """
    text = _try_pymupdf(content)
    if text and len(text.strip()) >= _MIN_TEXT_LENGTH:
        logger.debug("PyMuPDF extracted %d chars", len(text))
        return text

    logger.info("PyMuPDF result too short (%d chars), falling back to pdfminer", len(text or ""))
    text = _try_pdfminer(content)
    if text and len(text.strip()) >= _MIN_TEXT_LENGTH:
        logger.debug("pdfminer extracted %d chars", len(text))
        return text

    raise PDFParserError(
        "Could not extract meaningful text from the PDF. "
        "The file may be scanned/image-only or password-protected."
    )


def _try_pymupdf(content: bytes) -> str | None:
    """Attempt extraction with PyMuPDF (fitz). Returns None on any error."""
    try:
        import fitz  # PyMuPDF

        with fitz.open(stream=content, filetype="pdf") as doc:
            text_parts: list[str] = []
            for page in doc:
                text_parts.append(str(page.get_text()))  # type: ignore[arg-type]
        return "\n".join(text_parts)
    except Exception as exc:
        logger.warning("PyMuPDF extraction failed: %s", exc)
        return None


def _try_pdfminer(content: bytes) -> str | None:
    """Attempt extraction with pdfminer.six. Returns None on any error."""
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract

        return pdfminer_extract(io.BytesIO(content))
    except Exception as exc:
        logger.warning("pdfminer extraction failed: %s", exc)
        return None
