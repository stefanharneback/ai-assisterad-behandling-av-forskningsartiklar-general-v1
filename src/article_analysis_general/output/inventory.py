from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from article_analysis_general.store.record import Article


INVENTORY_FILENAME = "inventory.csv"

# A human-readable early view of the result contract: one row per article with
# the bibliographic and identity columns that exist from M1, before the full
# Resultat.xlsx output arrives in M6.
INVENTORY_COLUMNS = [
    "doc_id",
    "title",
    "published_year",
    "doi",
    "venue",
    "text_layer",
    "extraction_status",
    "source_databases",
    "file_names",
    "relative_paths",
]


def write_inventory(articles: list[Article], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INVENTORY_COLUMNS)
        writer.writeheader()
        for article in articles:
            writer.writerow(_inventory_row(article))


def _inventory_row(article: Article) -> dict[str, str]:
    return {
        "doc_id": article.doc_id,
        "title": article.title or "",
        "published_year": "" if article.published_year is None else str(article.published_year),
        "doi": article.doi or "",
        "venue": article.venue or "",
        "text_layer": article.text_layer,
        "extraction_status": article.extraction_status,
        "source_databases": "; ".join(_unique(source.source_database for source in article.sources)),
        "file_names": "; ".join(source.file_name for source in article.sources),
        "relative_paths": "; ".join(source.relative_path for source in article.sources),
    }


def _unique(values: Iterable[str]) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        if value not in seen:
            seen[value] = None
    return list(seen)
