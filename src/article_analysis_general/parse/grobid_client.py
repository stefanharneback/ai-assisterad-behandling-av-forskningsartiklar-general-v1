from __future__ import annotations

from pathlib import Path


class GrobidClient:
    """Thin future adapter for GROBID TEI extraction."""

    def __init__(self, base_url: str = "http://localhost:8070") -> None:
        self.base_url = base_url.rstrip("/")

    def process_fulltext_document(self, pdf_path: Path) -> str:
        raise NotImplementedError("GROBID integration is planned for M2.")

