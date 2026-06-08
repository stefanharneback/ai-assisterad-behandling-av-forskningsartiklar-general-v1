from __future__ import annotations

from pathlib import Path

from article_analysis_general.parse.local import extract_pdf_text


def parse_with_local_fallback(pdf_path: Path) -> str:
    return extract_pdf_text(pdf_path).full_text
