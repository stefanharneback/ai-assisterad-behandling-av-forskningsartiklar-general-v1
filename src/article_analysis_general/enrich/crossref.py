from __future__ import annotations


class CrossrefClient:
    """Future Crossref client for DOI resolution and bibliographic metadata."""

    def __init__(self, email: str | None = None) -> None:
        self.email = email

    def search_by_title(self, title: str) -> dict[str, object]:
        raise NotImplementedError("Crossref DOI resolution is planned for M3.")

