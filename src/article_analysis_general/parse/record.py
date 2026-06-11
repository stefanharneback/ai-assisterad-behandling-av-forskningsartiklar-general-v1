from __future__ import annotations

from pathlib import Path, PurePosixPath

from article_analysis_general.parse.local import parse_pdf_document
from article_analysis_general.store.record import Article, ArticleRecord, ArticleSource, ExtractionStatus, PageRecord


def build_local_article_record(article: Article, *, corpus: Path) -> ArticleRecord:
    if article.text_layer != "text":
        return ArticleRecord(article=article)

    try:
        parsed = parse_pdf_document(_source_path(corpus, article.sources[0]), doc_id=article.doc_id)
    except Exception:
        return ArticleRecord(article=article.model_copy(update={"extraction_status": "failed"}))

    extraction_status: ExtractionStatus = "ok" if parsed.sections else "partial"
    parsed_article = article.model_copy(update={"extraction_status": extraction_status})
    return ArticleRecord(
        article=parsed_article,
        full_text=parsed.full_text,
        pages=[
            PageRecord(
                page_number=page.page_number,
                text=page.text,
                start_offset=page.start_offset,
                end_offset=page.end_offset,
            )
            for page in parsed.pages
        ],
        sections=parsed.sections,
        chunks=parsed.chunks,
    )


def _source_path(corpus: Path, source: ArticleSource) -> Path:
    return corpus.joinpath(*PurePosixPath(source.relative_path).parts)
