from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from article_analysis_general.store.record import Article, ArticleSource
from article_analysis_general.store.run import RunManifest, new_run_id, write_run


def _article(doc_id: str, source_database: str, text_layer: str) -> Article:
    return Article(
        doc_id=doc_id,
        file_hash=doc_id,
        sources=[ArticleSource(file_name=f"{doc_id}.pdf", relative_path=f"{source_database}/{doc_id}.pdf", source_database=source_database)],
        text_layer=text_layer,
    )


class RunOutputTests(unittest.TestCase):
    def test_new_run_id_uses_utc_timestamp(self) -> None:
        moment = datetime(2026, 6, 8, 10, 15, 30, tzinfo=UTC)

        self.assertEqual(new_run_id(moment), "run-20260608T101530Z")

    def test_write_run_writes_record_per_article_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            articles = [_article("aaa", "SCOPUS", "text"), _article("bbb", "ERIC", "scanned")]

            write_run(articles, corpus="Forskning", base_dir=base, run_id="run-test")

            run_dir = base / "run-test"
            self.assertTrue((run_dir / "records" / "aaa.json").exists())
            self.assertTrue((run_dir / "records" / "bbb.json").exists())
            self.assertTrue((run_dir / "manifest.json").exists())

            loaded = Article.model_validate_json((run_dir / "records" / "aaa.json").read_text(encoding="utf-8"))
            self.assertEqual(loaded.doc_id, "aaa")

    def test_manifest_counts_articles_sources_and_text_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            articles = [_article("aaa", "SCOPUS", "text"), _article("bbb", "ERIC", "text"), _article("ccc", "ERIC", "scanned")]

            manifest = write_run(articles, corpus="Forskning", base_dir=Path(tmp), run_id="run-test")

            self.assertEqual(manifest.article_count, 3)
            self.assertEqual(manifest.source_count, 3)
            self.assertEqual(manifest.text_layer_counts["text"], 2)
            self.assertEqual(manifest.text_layer_counts["scanned"], 1)

    def test_manifest_round_trips_from_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write_run([_article("aaa", "SCOPUS", "text")], corpus="Forskning", base_dir=base, run_id="run-test")

            loaded = RunManifest.model_validate_json((base / "run-test" / "manifest.json").read_text(encoding="utf-8"))

            self.assertEqual(loaded.run_id, "run-test")
            self.assertEqual(loaded.corpus, "Forskning")


if __name__ == "__main__":
    unittest.main()
