"""
Module 1 – Document Parser
Supports PDF (.pdf) and Word (.docx) files.
Returns clean text plus metadata.
"""
from __future__ import annotations
import io
import re
from pathlib import Path
from typing import Any


def _clean(text: str) -> str:
    """Normalise whitespace and remove null bytes."""
    text = text.replace("\x00", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def parse_pdf(file_obj) -> dict[str, Any]:
    """Parse a PDF file-like object. Returns dict with text, pages, metadata."""
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required: pip install pdfplumber")

    pages_text: list[str] = []
    with pdfplumber.open(file_obj) as pdf:
        metadata = pdf.metadata or {}
        for page in pdf.pages:
            t = page.extract_text() or ""
            pages_text.append(t)

    full_text = "\n\n".join(pages_text)
    return {
        "text": _clean(full_text),
        "pages": len(pages_text),
        "metadata": metadata,
        "file_type": "pdf",
    }


def parse_docx(file_obj) -> dict[str, Any]:
    """Parse a DOCX file-like object."""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required: pip install python-docx")

    doc = Document(file_obj)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    full_text = "\n\n".join(paragraphs)
    return {
        "text": _clean(full_text),
        "pages": max(1, len(paragraphs) // 20),  # estimate
        "metadata": {"title": doc.core_properties.title or ""},
        "file_type": "docx",
    }


def parse_txt(file_obj) -> dict[str, Any]:
    """Parse a plain text file."""
    if hasattr(file_obj, "read"):
        content = file_obj.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
    else:
        content = str(file_obj)
    return {
        "text": _clean(content),
        "pages": max(1, len(content) // 3000),
        "metadata": {},
        "file_type": "txt",
    }


def parse_document(file_obj, filename: str = "") -> dict[str, Any]:
    """
    Auto-detect file type and parse.
    `file_obj` can be a Streamlit UploadedFile, BytesIO, or path string.
    """
    name = filename or getattr(file_obj, "name", "")
    suffix = Path(name).suffix.lower()

    # Reset stream position if possible
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    if suffix == ".pdf":
        result = parse_pdf(file_obj)
    elif suffix in (".docx", ".doc"):
        result = parse_docx(file_obj)
    elif suffix == ".txt":
        result = parse_txt(file_obj)
    else:
        # Try PDF first, fall back to text
        try:
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            result = parse_pdf(file_obj)
        except Exception:
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            result = parse_txt(file_obj)

    result["filename"] = name
    result["word_count"] = len(result["text"].split())
    result["char_count"] = len(result["text"])
    return result
