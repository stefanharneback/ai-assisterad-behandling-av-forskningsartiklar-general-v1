from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from article_analysis_general import __version__
from article_analysis_general.store.record import Article, TextLayerStatus


RECORDS_DIRNAME = "records"
MANIFEST_FILENAME = "manifest.json"
RecordBuilder = Callable[[Article], BaseModel]


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
    record_builder: RecordBuilder | None = None,
) -> RunManifest:
    """Write one canonical JSON record per article plus a run manifest.

    An auto-generated ``run_id`` (``run_id=None``) never overwrites an existing
    run: a numeric suffix is appended until a fresh directory is created, so two
    ingests in the same second cannot clobber each other's history. An explicit
    ``run_id`` is idempotent and reuses its directory, refreshing its records in
    place.
    """
    moment = now or datetime.now(UTC)
    if run_id is None:
        run_dir = _create_unique_run_dir(base_dir, new_run_id(moment))
    else:
        run_dir = base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
    resolved_run_id = run_dir.name

    records_dir = run_dir / RECORDS_DIRNAME
    records_dir.mkdir(parents=True, exist_ok=True)

    for article in articles:
        record_path = records_dir / f"{article.doc_id}.json"
        record = record_builder(article) if record_builder is not None else article
        record_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")

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


def _create_unique_run_dir(base_dir: Path, run_id: str) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    candidate = base_dir / run_id
    suffix = 2
    while True:
        try:
            # Atomic create-or-fail so concurrent ingests never share a run dir.
            candidate.mkdir(exist_ok=False)
            return candidate
        except FileExistsError:
            candidate = base_dir / f"{run_id}-{suffix}"
            suffix += 1
