from __future__ import annotations

import tempfile
import unittest
import os
from pathlib import Path

from article_analysis_general.ingest.discovery import discover_articles, iter_pdf_paths, readable_file_path, sha256_file


class DiscoveryTests(unittest.TestCase):
    def test_doc_id_is_based_on_file_bytes_not_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "A" / "paper.pdf"
            second = root / "B" / "renamed.pdf"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_bytes(b"same pdf bytes")
            second.write_bytes(b"same pdf bytes")

            self.assertEqual(sha256_file(first), sha256_file(second))

    def test_discover_articles_deduplicates_identical_pdf_bytes_as_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "SCOPUS" / "paper.pdf"
            second = root / "ERIC" / "same-paper.pdf"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_bytes(b"same pdf bytes")
            second.write_bytes(b"same pdf bytes")

            articles = discover_articles(root)

            self.assertEqual(len(articles), 1)
            self.assertEqual(articles[0].doc_id, sha256_file(first))
            self.assertEqual({source.source_database for source in articles[0].sources}, {"SCOPUS", "ERIC"})

    def test_discover_articles_records_source_folder_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "SCOPUS" / "Paper.PDF"
            pdf.parent.mkdir()
            pdf.write_bytes(b"pdf bytes")

            articles = discover_articles(root)

            self.assertEqual(len(articles), 1)
            self.assertEqual(articles[0].sources[0].source_database, "SCOPUS")
            self.assertEqual(articles[0].doc_id, sha256_file(pdf))
            self.assertEqual(articles[0].sources[0].relative_path, "SCOPUS/Paper.PDF")

    def test_iter_pdf_paths_is_recursive_and_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one.pdf").write_bytes(b"1")
            nested = root / "nested"
            nested.mkdir()
            (nested / "two.PDF").write_bytes(b"2")
            (nested / "ignore.txt").write_text("ignore", encoding="utf-8")

            names = [path.name for path in iter_pdf_paths(root)]

            self.assertEqual(names, ["one.pdf", "two.PDF"])

    @unittest.skipUnless(os.name == "nt", "Windows extended paths are only used on Windows")
    def test_readable_file_path_uses_windows_extended_path_prefix(self) -> None:
        path = Path.cwd() / "Forskning" / "long-name.pdf"

        self.assertTrue(readable_file_path(path).startswith("\\\\?\\"))


if __name__ == "__main__":
    unittest.main()
