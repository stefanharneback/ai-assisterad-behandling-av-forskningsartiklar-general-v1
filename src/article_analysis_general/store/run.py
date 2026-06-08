from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from article_analysis_general import __version__
from article_analysis_general.store.record import Article, TextLayerStatus


RECORDS_DIRNAME = "records"
MANIFEST_FILENAME = "manifest.json"


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    run_id: str
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tool_version: str = __version__
    corpus: str
    article_count: int = Field(ge=0)
    source_count: int = Field(ge=0)
    text_layer_counts: dict[TextLayerStatus, int] = Field(default_factory=dict)


def new_run_id(now: datetime | None = None) -> str:
    moment = now or datetime.now(UTC)
    return moment.strftime("run-%Y%m%dT%H%M%SZ")


def write_run(
    articles: list[Article],
    *,
    corpus: str,
    base_dir: Path = Path("runs"),
    run_id: str | None = None,
    now: datetime | None = None,
) -> RunManifest:
    """Write one canonical JSON record per article plus a run manifest.

    Records are keyed by ``doc_id``, so re-running the same ``run_id`` overwrites
    the same files idempotently rather than accumulating duplicates.
    """
    moment = now or datetime.now(UTC)
    resolved_run_id = run_id or new_run_id(moment)
    run_dir = base_dir / resolved_run_id
    records_dir = run_dir / RECORDS_DIRNAME
    records_dir.mkdir(parents=True, exist_ok=True)

    for article in articles:
        record_path = records_dir / f"{article.doc_id}.json"
        record_path.write_text(article.model_dump_json(indent=2), encoding="utf-8")

    manifest = RunManifest(
        run_id=resolved_run_id,
        created_at_utc=moment,
        corpus=corpus,
        article_count=len(articles),
        source_count=sum(len(article.sources) for article in articles),
        text_layer_counts=dict(Counter(article.text_layer for article in articles)),
    )
    (run_dir / MANIFEST_FILENAME).write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return manifest
