from __future__ import annotations


class UnpaywallClient:
    """Future Unpaywall client for legal open-access fulltext links."""

    def __init__(self, email: str) -> None:
        self.email = email

    def lookup_doi(self, doi: str) -> dict[str, object]:
        raise NotImplementedError("Unpaywall enrichment is planned for M3.")

