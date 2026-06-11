from __future__ import annotations

import hashlib
import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from article_analysis_general.store.record import Article, ArticleSource, TextLayerStatus


# A PDF with a real text layer yields characters from page.get_text; a scanned
# (image-only) PDF yields (almost) none. The threshold ignores stray artifacts
# like page numbers so a single OCR-free header does not look like a text layer.
MIN_TEXT_LAYER_CHARS = 32


@dataclass(frozen=True)
class TextLayerInspection:
    status: TextLayerStatus
    page_count: int | None = None
    text_char_count: int | None = None
    error: str | None = None


def iter_pdf_paths(corpus: Path) -> list[Path]:
    paths: list[Path] = []
    if not corpus.exists():
        return paths
    for root, dirs, files in os.walk(corpus):
        dirs.sort(key=str.casefold)
        for file_name in sorted(files, key=str.casefold):
            if file_name.lower().endswith(".pdf"):
                paths.append(Path(root) / file_name)
    return paths


def discover_articles(corpus: Path) -> list[Article]:
    articles_by_doc_id: dict[str, Article] = {}
    for pdf_path in iter_pdf_paths(corpus):
        file_hash = sha256_file(pdf_path)
        text_layer = inspect_text_layer(pdf_path)
        source = ArticleSource(
            file_name=pdf_path.name,
            relative_path=normalized_relative_path(corpus, pdf_path),
            source_database=source_folder_for(corpus, pdf_path),
        )
        article = articles_by_doc_id.get(file_hash)
        if article is None:
            articles_by_doc_id[file_hash] = Article(
                doc_id=file_hash,
                file_hash=file_hash,
                sources=[source],
                text_layer=text_layer.status,
                page_count=text_layer.page_count,
                text_char_count=text_layer.text_char_count,
                text_layer_error=text_layer.error,
                extraction_status="not_started",
            )
        elif source not in article.sources:
            article.sources.append(source)
    return list(articles_by_doc_id.values())


def detect_text_layer(path: Path) -> TextLayerStatus:
    return inspect_text_layer(path).status


def inspect_text_layer(path: Path) -> TextLayerInspection:
    try:
        with fitz.open(readable_file_path(path)) as doc:
            page_count = doc.page_count
            if page_count == 0:
                return TextLayerInspection(status="unknown", page_count=0, text_char_count=0)
            char_count = 0
            for page_number in range(page_count):
                page = doc.load_page(page_number)
                char_count += len(page.get_text("text").strip())
        status: TextLayerStatus = "text" if char_count >= MIN_TEXT_LAYER_CHARS else "scanned"
        return TextLayerInspection(status=status, page_count=page_count, text_char_count=char_count)
    except Exception as exc:
        # Unreadable, encrypted or non-PDF bytes: leave the layer undetermined
        # so later parsing milestones can refine it instead of guessing now.
        return TextLayerInspection(status="unknown", error=f"{type(exc).__name__}: {exc}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(readable_file_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def readable_file_path(path: Path) -> str:
    if os.name != "nt":
        return str(path)

    path_text = str(path.resolve(strict=False))
    if path_text.startswith("\\\\?\\"):
        return path_text
    if path_text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + path_text[2:]
    return "\\\\?\\" + path_text


def normalized_relative_path(corpus: Path, path: Path) -> str:
    try:
        relative = path.relative_to(corpus)
    except ValueError:
        relative = path
    return unicodedata.normalize("NFC", relative.as_posix())


def source_folder_for(corpus: Path, path: Path) -> str:
    try:
        relative = path.relative_to(corpus)
    except ValueError:
        return ""
    return unicodedata.normalize("NFC", relative.parts[0]) if relative.parts else ""
