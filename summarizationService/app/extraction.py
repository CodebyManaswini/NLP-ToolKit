"""
Text extraction helpers for the Summarization Service.
Supports PDF, DOCX, and plain TXT uploads.
"""

import io

from docx import Document
from pypdf import PdfReader


class UnsupportedFileType(Exception):
    pass


class EmptyDocumentError(Exception):
    pass


def extract_text(filename: str, file_bytes: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        text = _extract_pdf(file_bytes)
    elif lower.endswith(".docx"):
        text = _extract_docx(file_bytes)
    elif lower.endswith(".txt"):
        text = _extract_txt(file_bytes)
    else:
        raise UnsupportedFileType(
            f"Unsupported file type for '{filename}'. Use .pdf, .docx, or .txt."
        )

    text = text.strip()
    if not text:
        raise EmptyDocumentError("No extractable text found in the uploaded document.")
    return text


def _extract_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _extract_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs)


def _extract_txt(file_bytes: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="replace")