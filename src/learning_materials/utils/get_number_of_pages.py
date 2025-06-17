import logging
from typing import IO, Optional
import uuid
import io
import PyPDF2
from django.db import transaction
import re


logger = logging.getLogger(__name__)

# Fast regexes
_PAGES_DICT_RE = re.compile(rb"/Type\s*/Pages[^>]+?/Count\s+(\d+)", re.DOTALL)
_PAGE_MARK_RE = re.compile(rb"/Type\s*/Page\b")

PDF_HEADER = b"%PDF-"


def is_pdf(file_obj: IO[bytes]) -> bool:
    """Detect PDF by magic bytes so we don't rely on MIME."""
    pos = file_obj.tell()
    try:
        file_obj.seek(0)
        return file_obj.read(5) == PDF_HEADER
    finally:
        file_obj.seek(pos)


def cheap_pdf_page_count(file_obj: IO[bytes]) -> Optional[int]:
    """
    Fast-but-best-effort page count.
    Returns an int, or None if we couldn’t determine it cheaply.
    Leaves the file pointer unchanged.
    """
    if not is_pdf(file_obj):
        return None

    start = file_obj.tell()
    try:
        # ---------- FAST PATH: look for /Count in first 128 kB ----------
        file_obj.seek(0)
        head = file_obj.read(128_000)
        m = _PAGES_DICT_RE.search(head)
        if m:
            return int(m.group(1))

        # ---------- SLOW PATH: scan literal /Type /Page in the whole file ----------
        file_obj.seek(0)
        pages = 0
        overlap = b""
        for chunk in iter(lambda: file_obj.read(64_000), b""):
            data = overlap + chunk
            pages += len(_PAGE_MARK_RE.findall(data))
            overlap = data[-20:]                # keep tail for split markers
        return pages if pages else None         # 0 pages ⇒ treat as unknown
    finally:
        file_obj.seek(start)


def get_num_pages(file_obj: IO[bytes]) -> int:
    """
    Public API: cheap first, then precise.
    Guaranteed to return an int (0 = unknown / failed).
    """
    count = cheap_pdf_page_count(file_obj)
    if count is not None:
        return count

    # ---------- fallback: PyPDF2 (accurate, but heavier) ----------
    try:
        file_obj.seek(0)
        reader = PyPDF2.PdfReader(file_obj, strict=False)
        return len(reader.pages)
    except Exception as exc:
        logger.warning("Precise page count failed for %s: %s", file_obj, exc)
        return 0