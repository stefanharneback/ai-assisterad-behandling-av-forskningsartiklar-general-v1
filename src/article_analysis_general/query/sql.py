from __future__ import annotations


ARTICLE_REFERENCES_TABLE = "article_references"


def shared_references_query() -> str:
    raise NotImplementedError(f"Shared-reference SQL is planned for M4 using {ARTICLE_REFERENCES_TABLE}.")
