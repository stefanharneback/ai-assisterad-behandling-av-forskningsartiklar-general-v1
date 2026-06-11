from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from article_analysis_general.output.inventory import write_inventory
from article_analysis_general.store.record import Article, ArticleSource


def _read_rows(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class InventoryTests(unittest.TestCase):
    def test_write_inventory_writes_one_row_per_article(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inventory.csv"
            article = Article(
                doc_id="aaa",
                file_hash="aaa",
                sources=[
                    ArticleSource(file_name="paper.pdf", relative_path="SCOPUS/paper.pdf", source_database="SCOPUS"),
                    ArticleSource(file_name="dup.pdf", relative_path="ERIC/dup.pdf", source_database="ERIC"),
                ],
                title="A Study",
                published_year=2024,
                text_layer="text",
                page_count=12,
                text_char_count=3456,
            )

            write_inventory([article], path)

            rows = _read_rows(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["doc_id"], "aaa")
            self.assertEqual(rows[0]["title"], "A Study")
            self.assertEqual(rows[0]["published_year"], "2024")
            self.assertEqual(rows[0]["text_layer"], "text")
            self.assertEqual(rows[0]["page_count"], "12")
            self.assertEqual(rows[0]["text_char_count"], "3456")
            self.assertEqual(rows[0]["text_layer_error"], "")
            self.assertEqual(rows[0]["source_databases"], "SCOPUS; ERIC")

    def test_write_inventory_renders_missing_fields_as_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inventory.csv"
            article = Article(
                doc_id="bbb",
                file_hash="bbb",
                sources=[ArticleSource(file_name="b.pdf", relative_path="X/b.pdf", source_database="X")],
            )

            write_inventory([article], path)

            rows = _read_rows(path)
            self.assertEqual(rows[0]["title"], "")
            self.assertEqual(rows[0]["published_year"], "")
            self.assertEqual(rows[0]["doi"], "")
            self.assertEqual(rows[0]["text_layer"], "unknown")
            self.assertEqual(rows[0]["page_count"], "")
            self.assertEqual(rows[0]["text_char_count"], "")
            self.assertEqual(rows[0]["text_layer_error"], "")


if __name__ == "__main__":
    unittest.main()
