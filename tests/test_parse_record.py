from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import fitz  # PyMuPDF

from article_analysis_general.ingest.discovery import discover_articles
from article_analysis_general.parse.record import build_local_article_record


def _write_text_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()


class ParseRecordTests(unittest.TestCase):
    def test_build_local_article_record_adds_sections_and_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "Forskning"
            pdf = corpus / "SCOPUS" / "paper.pdf"
            pdf.parent.mkdir(parents=True)
            _write_text_pdf(pdf, "Abstract\nA concise abstract.\n\nMethods\nMethod details.")
            article = discover_articles(corpus)[0]

            record = build_local_article_record(article, corpus=corpus)

            self.assertEqual(record.article.extraction_status, "ok")
            self.assertEqual([section.normalized_type for section in record.sections], ["abstract", "method"])
            self.assertGreaterEqual(len(record.chunks), 2)

    def test_build_local_article_record_leaves_scanned_pdf_for_later_ocr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "Forskning"
            pdf = corpus / "ERIC" / "blank.pdf"
            pdf.parent.mkdir(parents=True)
            document = fitz.open()
            document.new_page()
            document.save(str(pdf))
            document.close()
            article = discover_articles(corpus)[0]

            record = build_local_article_record(article, corpus=corpus)

            self.assertEqual(record.article.text_layer, "scanned")
            self.assertEqual(record.article.extraction_status, "not_started")
            self.assertEqual(record.sections, [])
            self.assertEqual(record.chunks, [])


if __name__ == "__main__":
    unittest.main()
