from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import fitz  # PyMuPDF

from article_analysis_general.parse.fallback import parse_with_local_fallback
from article_analysis_general.parse.local import (
    PageText,
    ParsedPdfText,
    chunk_sections,
    extract_pdf_text,
    parse_pdf_document,
    split_sections,
)
from article_analysis_general.store.record import Provenance, Section


def _write_text_pdf(path: Path, pages: list[str]) -> None:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()


class LocalParseTests(unittest.TestCase):
    def test_extract_pdf_text_records_page_offsets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "paper.pdf"
            _write_text_pdf(pdf, ["First page text.", "Second page text."])

            parsed = extract_pdf_text(pdf)

            self.assertEqual(len(parsed.pages), 2)
            self.assertIn("First page text.", parsed.full_text)
            self.assertIn("Second page text.", parsed.full_text)
            self.assertEqual(parsed.pages[0].page_number, 1)
            self.assertEqual(parsed.pages[0].start_offset, 0)
            self.assertGreater(parsed.pages[1].start_offset, parsed.pages[0].end_offset)

    def test_split_sections_detects_article_headings_and_front_matter(self) -> None:
        text = (
            "Article Title\n\n"
            "Abstract\n"
            "Abstract text.\n\n"
            "1 Introduction\n"
            "Intro text.\n\n"
            "Methods\n"
            "Method text.\n\n"
            "Results\n"
            "Result text.\n\n"
            "References\n"
            "Ref text."
        )
        parsed = ParsedPdfText(full_text=text, pages=[PageText(page_number=1, text=text, start_offset=0, end_offset=len(text))])

        sections = split_sections(parsed, doc_id="doc")

        self.assertEqual([section.normalized_type for section in sections], ["other", "abstract", "intro", "method", "results", "references"])
        self.assertEqual(sections[0].heading, "Front Matter")
        self.assertEqual(sections[1].heading, "Abstract")
        self.assertEqual(sections[1].text, "Abstract text.")
        self.assertEqual(sections[1].provenance.start_offset, text.index("Abstract text."))

    def test_split_sections_detects_roman_numbered_composite_headings(self) -> None:
        text = (
            "I. INTRODUCTION\n"
            "Intro text.\n\n"
            "III. METHODOLOGY\n"
            "Method text.\n\n"
            "IV. RESULTS AND ANALYSIS\n"
            "Result text.\n\n"
            "V. DISCUSSION AND CONCLUSIONS\n"
            "Discussion text.\n\n"
            "REFERENCES\n"
            "Ref text."
        )
        parsed = ParsedPdfText(full_text=text, pages=[PageText(page_number=1, text=text, start_offset=0, end_offset=len(text))])

        sections = split_sections(parsed, doc_id="doc")

        self.assertEqual(
            [section.normalized_type for section in sections],
            ["intro", "method", "results", "discussion", "references"],
        )
        self.assertEqual(sections[1].heading, "III. METHODOLOGY")
        self.assertEqual(sections[2].text, "Result text.")

    def test_parse_pdf_document_builds_sections_and_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "paper.pdf"
            _write_text_pdf(pdf, ["Abstract\nA concise abstract.\n\nMethods\nMethod details."])

            parsed = parse_pdf_document(pdf, doc_id="doc", max_chunk_chars=80)

            self.assertEqual([section.normalized_type for section in parsed.sections], ["abstract", "method"])
            self.assertGreaterEqual(len(parsed.chunks), 2)
            self.assertEqual(parsed.chunks[0].doc_id, "doc")
            self.assertEqual(parsed.chunks[0].section_id, parsed.sections[0].section_id)

    def test_chunk_sections_splits_long_section_with_provenance(self) -> None:
        section = Section(
            section_id="doc:section:0001",
            doc_id="doc",
            heading="Methods",
            normalized_type="method",
            text="alpha beta gamma delta epsilon zeta eta theta iota kappa",
            provenance=Provenance(page_start=2, page_end=3, start_offset=10, end_offset=66),
        )

        chunks = chunk_sections([section], max_chars=24, overlap=6)

        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].provenance.section_id, section.section_id)
        self.assertEqual(chunks[0].provenance.page_start, 2)
        self.assertEqual(chunks[0].provenance.start_offset, 10)
        self.assertGreater(chunks[1].provenance.start_offset or 0, 10)

    def test_chunk_sections_derives_page_provenance_from_offsets_when_pages_are_available(self) -> None:
        first_page = "First page content."
        second_page = "Second page content."
        full_text = f"{first_page}\n\n{second_page}"
        pages = [
            PageText(page_number=1, text=first_page, start_offset=0, end_offset=len(first_page)),
            PageText(
                page_number=2,
                text=second_page,
                start_offset=len(first_page) + 2,
                end_offset=len(full_text),
            ),
        ]
        section = Section(
            section_id="doc:section:0001",
            doc_id="doc",
            heading="Methods",
            normalized_type="method",
            text=full_text,
            provenance=Provenance(page_start=1, page_end=2, start_offset=0, end_offset=len(full_text)),
        )

        chunks = chunk_sections([section], pages=pages, max_chars=len(first_page) + 1, overlap=0)

        self.assertEqual(chunks[0].provenance.page_start, 1)
        self.assertEqual(chunks[0].provenance.page_end, 1)
        self.assertEqual(chunks[1].provenance.page_start, 2)
        self.assertEqual(chunks[1].provenance.page_end, 2)

    def test_parse_with_local_fallback_returns_pdf_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "paper.pdf"
            _write_text_pdf(pdf, ["Fallback text."])

            self.assertIn("Fallback text.", parse_with_local_fallback(pdf))


if __name__ == "__main__":
    unittest.main()
