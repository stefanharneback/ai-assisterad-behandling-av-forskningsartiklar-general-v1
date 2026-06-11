from __future__ import annotations

import tempfile
import unittest
import os
from pathlib import Path

import fitz  # PyMuPDF

from article_analysis_general.ingest.discovery import (
    detect_text_layer,
    discover_articles,
    inspect_text_layer,
    iter_pdf_paths,
    readable_file_path,
    sha256_file,
)


def _write_text_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()


def _write_text_pdf_pages(path: Path, pages: list[str]) -> None:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()


def _write_blank_pdf(path: Path) -> None:
    document = fitz.open()
    document.new_page()
    document.save(str(path))
    document.close()


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

    def test_detect_text_layer_finds_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "text.pdf"
            _write_text_pdf(pdf, "Method, results and discussion of the study.")

            self.assertEqual(detect_text_layer(pdf), "text")

    def test_detect_text_layer_marks_image_only_pdf_as_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "blank.pdf"
            _write_blank_pdf(pdf)

            self.assertEqual(detect_text_layer(pdf), "scanned")

    def test_inspect_text_layer_records_openable_pdf_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "text.pdf"
            _write_text_pdf(pdf, "Method, results and discussion of the study.")

            inspection = inspect_text_layer(pdf)

            self.assertEqual(inspection.status, "text")
            self.assertEqual(inspection.page_count, 1)
            self.assertGreater(inspection.text_char_count or 0, 0)
            self.assertIsNone(inspection.error)

    def test_inspect_text_layer_counts_text_across_all_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "text.pdf"
            first_page = "Method, results and discussion of the study."
            second_page = "Second page text that must also be counted."
            _write_text_pdf_pages(pdf, [first_page, second_page])

            inspection = inspect_text_layer(pdf)

            self.assertEqual(inspection.status, "text")
            self.assertEqual(inspection.page_count, 2)
            self.assertGreater(inspection.text_char_count or 0, len(first_page))

    def test_detect_text_layer_is_unknown_for_non_pdf_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "broken.pdf"
            pdf.write_bytes(b"not a pdf")

            self.assertEqual(detect_text_layer(pdf), "unknown")

    def test_inspect_text_layer_records_error_for_unreadable_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "broken.pdf"
            pdf.write_bytes(b"not a pdf")

            inspection = inspect_text_layer(pdf)

            self.assertEqual(inspection.status, "unknown")
            self.assertIsNone(inspection.page_count)
            self.assertIsNone(inspection.text_char_count)
            self.assertIn("FileDataError", inspection.error or "")

    def test_discover_articles_sets_detected_text_layer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SCOPUS").mkdir()
            _write_text_pdf(root / "SCOPUS" / "paper.pdf", "Abstract, method and results section text.")

            articles = discover_articles(root)

            self.assertEqual(len(articles), 1)
            self.assertEqual(articles[0].text_layer, "text")
            self.assertEqual(articles[0].page_count, 1)
            self.assertGreater(articles[0].text_char_count or 0, 0)
            self.assertIsNone(articles[0].text_layer_error)

    @unittest.skipUnless(os.name == "nt", "Windows extended paths are only used on Windows")
    def test_readable_file_path_uses_windows_extended_path_prefix(self) -> None:
        path = Path.cwd() / "Forskning" / "long-name.pdf"

        self.assertTrue(readable_file_path(path).startswith("\\\\?\\"))


if __name__ == "__main__":
    unittest.main()
