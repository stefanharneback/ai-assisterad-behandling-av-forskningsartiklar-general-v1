from __future__ import annotations


class OpenAlexClient:
    """Future OpenAlex client for works, authors and citation graph enrichment."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def work_by_doi(self, doi: str) -> dict[str, object]:
        raise NotImplementedError("OpenAlex enrichment is planned for M3.")
