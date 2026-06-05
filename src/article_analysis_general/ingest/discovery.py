from __future__ import annotations

import hashlib
import os
import unicodedata
from pathlib import Path

from article_analysis_general.store.record import Article, ArticleSource


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
                extraction_status="not_started",
            )
        elif source not in article.sources:
            article.sources.append(source)
    return list(articles_by_doc_id.values())


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
