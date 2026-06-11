from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from article_analysis_general.ingest.discovery import readable_file_path
from article_analysis_general.store.record import Chunk, Provenance, Section, SectionType


DEFAULT_CHUNK_CHARS = 2_000
DEFAULT_CHUNK_OVERLAP = 200
PAGE_SEPARATOR = "\n\n"


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str
    start_offset: int
    end_offset: int


@dataclass(frozen=True)
class ParsedPdfText:
    full_text: str
    pages: list[PageText]


@dataclass(frozen=True)
class ParsedPdfDocument:
    full_text: str
    pages: list[PageText]
    sections: list[Section]
    chunks: list[Chunk]


@dataclass(frozen=True)
class _HeadingMatch:
    heading: str
    normalized_type: SectionType
    start_offset: int
    end_offset: int


_HEADING_PREFIX_RE = re.compile(r"^\s*(?:(?:\d+(?:\.\d+)*)|(?:[IVXLCDM]+))\.?\s+", re.IGNORECASE)
_HEADING_TRAILING_RE = re.compile(r"[\s:.\-–—]+$")

_SECTION_HEADINGS: dict[str, SectionType] = {
    "abstract": "abstract",
    "summary": "abstract",
    "sammanfattning": "abstract",
    "introduction": "intro",
    "background": "intro",
    "bakgrund": "intro",
    "methods": "method",
    "method": "method",
    "materials and methods": "method",
    "methodology": "method",
    "participants": "method",
    "procedure": "method",
    "procedures": "method",
    "sample": "method",
    "samples": "method",
    "data collection": "method",
    "data analysis": "method",
    "research design": "method",
    "study design": "method",
    "metod": "method",
    "results": "results",
    "result": "results",
    "results and analysis": "results",
    "findings": "results",
    "findings of research": "results",
    "resultat": "results",
    "discussion": "discussion",
    "discussion and conclusion": "discussion",
    "discussion and conclusions": "discussion",
    "diskussion": "discussion",
    "conclusion": "conclusion",
    "conclusions": "conclusion",
    "slutsats": "conclusion",
    "references": "references",
    "reference": "references",
    "bibliography": "references",
    "referenser": "references",
}


def parse_pdf_document(
    pdf_path: Path,
    *,
    doc_id: str,
    max_chunk_chars: int = DEFAULT_CHUNK_CHARS,
    chunk_overlap: int | None = None,
) -> ParsedPdfDocument:
    parsed_text = extract_pdf_text(pdf_path)
    sections = split_sections(parsed_text, doc_id=doc_id)
    resolved_overlap = _default_overlap(max_chunk_chars) if chunk_overlap is None else chunk_overlap
    chunks = chunk_sections(sections, max_chars=max_chunk_chars, overlap=resolved_overlap)
    return ParsedPdfDocument(
        full_text=parsed_text.full_text,
        pages=parsed_text.pages,
        sections=sections,
        chunks=chunks,
    )


def extract_pdf_text(pdf_path: Path) -> ParsedPdfText:
    pages: list[PageText] = []
    parts: list[str] = []
    offset = 0

    with fitz.open(readable_file_path(pdf_path)) as document:
        for page_index, page in enumerate(document):
            if parts:
                parts.append(PAGE_SEPARATOR)
                offset += len(PAGE_SEPARATOR)

            page_text = page.get_text("text")
            start_offset = offset
            end_offset = start_offset + len(page_text)
            pages.append(
                PageText(
                    page_number=page_index + 1,
                    text=page_text,
                    start_offset=start_offset,
                    end_offset=end_offset,
                )
            )
            parts.append(page_text)
            offset = end_offset

    return ParsedPdfText(full_text="".join(parts), pages=pages)


def split_sections(parsed_text: ParsedPdfText, *, doc_id: str) -> list[Section]:
    full_text = parsed_text.full_text
    headings = _find_headings(full_text)
    sections: list[Section] = []

    if not full_text.strip():
        return sections

    if not headings:
        section_text, start_offset, end_offset = _trimmed_span(full_text, 0, len(full_text))
        if not section_text:
            return sections
        return [
            _section(
                doc_id=doc_id,
                index=1,
                heading="Full Text",
                normalized_type="other",
                text=section_text,
                start_offset=start_offset,
                end_offset=end_offset,
                pages=parsed_text.pages,
            )
        ]

    first_heading = headings[0]
    front_text, front_start, front_end = _trimmed_span(full_text, 0, first_heading.start_offset)
    next_index = 1
    if front_text:
        sections.append(
            _section(
                doc_id=doc_id,
                index=next_index,
                heading="Front Matter",
                normalized_type="other",
                text=front_text,
                start_offset=front_start,
                end_offset=front_end,
                pages=parsed_text.pages,
            )
        )
        next_index += 1

    for heading_index, heading in enumerate(headings):
        raw_start = heading.end_offset
        raw_end = headings[heading_index + 1].start_offset if heading_index + 1 < len(headings) else len(full_text)
        section_text, start_offset, end_offset = _trimmed_span(full_text, raw_start, raw_end)
        if not section_text:
            start_offset = heading.start_offset
            end_offset = heading.end_offset
        sections.append(
            _section(
                doc_id=doc_id,
                index=next_index,
                heading=heading.heading,
                normalized_type=heading.normalized_type,
                text=section_text,
                start_offset=start_offset,
                end_offset=end_offset,
                pages=parsed_text.pages,
            )
        )
        next_index += 1

    return sections


def chunk_sections(
    sections: list[Section],
    *,
    max_chars: int = DEFAULT_CHUNK_CHARS,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap < 0:
        raise ValueError("overlap must not be negative")
    if overlap >= max_chars:
        raise ValueError("overlap must be smaller than max_chars")

    chunks: list[Chunk] = []
    for section in sections:
        section_start = section.provenance.start_offset
        if section_start is None or not section.text:
            continue

        start = 0
        section_chunk_index = 1
        while start < len(section.text):
            end = _chunk_end(section.text, start, max_chars)
            raw_chunk = section.text[start:end]
            chunk_text, trim_start, trim_end = _trimmed_text(raw_chunk)
            if chunk_text:
                start_offset = section_start + start + trim_start
                end_offset = section_start + start + trim_end
                chunks.append(
                    Chunk(
                        chunk_id=f"{section.section_id}:chunk:{section_chunk_index:04d}",
                        doc_id=section.doc_id,
                        section_id=section.section_id,
                        text=chunk_text,
                        provenance=Provenance(
                            page_start=section.provenance.page_start,
                            page_end=section.provenance.page_end,
                            section_id=section.section_id,
                            start_offset=start_offset,
                            end_offset=end_offset,
                        ),
                    )
                )
                section_chunk_index += 1

            if end >= len(section.text):
                break
            start = max(0, end - overlap)

    return chunks


def _find_headings(text: str) -> list[_HeadingMatch]:
    headings: list[_HeadingMatch] = []
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        normalized_type = _classify_heading(line)
        if normalized_type is not None:
            headings.append(
                _HeadingMatch(
                    heading=line.strip(),
                    normalized_type=normalized_type,
                    start_offset=offset,
                    end_offset=offset + len(raw_line),
                )
            )
        offset += len(raw_line)
    return headings


def _classify_heading(line: str) -> SectionType | None:
    candidate = line.strip()
    if not candidate or len(candidate) > 80:
        return None
    if len(candidate.split()) > 6 and candidate.lower() not in _SECTION_HEADINGS:
        return None

    candidate = _HEADING_PREFIX_RE.sub("", candidate)
    candidate = _HEADING_TRAILING_RE.sub("", candidate)
    normalized = " ".join(candidate.casefold().split())
    return _SECTION_HEADINGS.get(normalized)


def _section(
    *,
    doc_id: str,
    index: int,
    heading: str,
    normalized_type: SectionType,
    text: str,
    start_offset: int,
    end_offset: int,
    pages: list[PageText],
) -> Section:
    page_start = _page_number_for_offset(pages, start_offset)
    page_end = _page_number_for_offset(pages, max(start_offset, end_offset - 1))
    return Section(
        section_id=f"{doc_id}:section:{index:04d}",
        doc_id=doc_id,
        heading=heading,
        normalized_type=normalized_type,
        text=text,
        provenance=Provenance(
            page_start=page_start,
            page_end=page_end,
            start_offset=start_offset,
            end_offset=end_offset,
        ),
    )


def _page_number_for_offset(pages: list[PageText], offset: int) -> int | None:
    if not pages:
        return None
    for page in pages:
        if page.start_offset <= offset <= page.end_offset:
            return page.page_number
        if offset < page.start_offset:
            return page.page_number
    return pages[-1].page_number


def _trimmed_span(text: str, start: int, end: int) -> tuple[str, int, int]:
    raw = text[start:end]
    stripped, trim_start, trim_end = _trimmed_text(raw)
    return stripped, start + trim_start, start + trim_end


def _trimmed_text(text: str) -> tuple[str, int, int]:
    trim_start = len(text) - len(text.lstrip())
    trim_end = len(text.rstrip())
    return text[trim_start:trim_end], trim_start, trim_end


def _chunk_end(text: str, start: int, max_chars: int) -> int:
    hard_end = min(len(text), start + max_chars)
    if hard_end >= len(text):
        return hard_end

    minimum = start + max(max_chars // 2, 1)
    candidates = [
        text.rfind("\n\n", start, hard_end),
        text.rfind("\n", start, hard_end),
        text.rfind(" ", start, hard_end),
    ]
    split_at = max(candidates)
    if split_at >= minimum:
        return split_at
    return hard_end


def _default_overlap(max_chars: int) -> int:
    return min(DEFAULT_CHUNK_OVERLAP, max(max_chars // 10, 0))
