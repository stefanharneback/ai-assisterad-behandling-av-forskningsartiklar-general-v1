from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ExtractionStatus = Literal["not_started", "ok", "partial", "failed"]
SectionType = Literal["abstract", "intro", "method", "results", "discussion", "conclusion", "references", "other"]
QuestionMethod = Literal["sql", "long-context", "rag"]
AnswerStatus = Literal["found", "not_found", "unclear"]
AnswerScope = Literal["article", "corpus", "run", "comparison"]
TextLayerStatus = Literal["text", "scanned", "unknown"]
AuthorshipRole = Literal["article", "reference", "external_work"]


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int | None = Field(default=None, ge=1)
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    section_id: str | None = None
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, ge=0)


class ArticleSource(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    source_database: str = ""
    relative_path: str
    file_name: str


class Author(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    author_id: str
    display_name: str
    openalex_id: str | None = None
    orcid: str | None = None
    institutions: list[str] = Field(default_factory=list)


class Authorship(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    work_id: str
    author_id: str
    role: AuthorshipRole
    position: int | None = Field(default=None, ge=1)


class Article(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    doc_id: str
    file_hash: str
    sources: list[ArticleSource] = Field(min_length=1)
    title: str | None = None
    author_ids: list[str] = Field(default_factory=list)
    published_year: int | None = None
    doi: str | None = None
    venue: str | None = None
    abstract: str | None = None
    text_layer: TextLayerStatus = "unknown"
    page_count: int | None = Field(default=None, ge=0)
    text_char_count: int | None = Field(default=None, ge=0)
    text_layer_error: str | None = None
    extraction_status: ExtractionStatus = "not_started"
    confidence: float | None = Field(default=None, ge=0, le=1)
    topics: list[str] = Field(default_factory=list)


class Section(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    section_id: str
    doc_id: str
    heading: str
    normalized_type: SectionType = "other"
    level: int = Field(default=1, ge=1)
    text: str
    provenance: Provenance = Field(default_factory=Provenance)


class Chunk(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    chunk_id: str
    doc_id: str
    section_id: str | None = None
    text: str
    provenance: Provenance = Field(default_factory=Provenance)


class Reference(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    reference_id: str
    citing_doc_id: str
    raw_text: str
    title: str | None = None
    raw_author_names: list[str] = Field(default_factory=list)
    author_ids: list[str] = Field(default_factory=list)
    published_year: int | None = None
    doi: str | None = None
    external_work_id: str | None = None
    match_confidence: float | None = Field(default=None, ge=0, le=1)


class ExternalWork(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    external_work_id: str
    title: str | None = None
    author_ids: list[str] = Field(default_factory=list)
    institutions: list[str] = Field(default_factory=list)
    published_year: int | None = None
    doi: str | None = None
    openalex_id: str | None = None
    semantic_scholar_id: str | None = None


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    question_id: str
    text: str
    method: QuestionMethod
    answer_schema: str
    version: str = "v1"


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    evidence_id: str
    doc_id: str
    quote: str
    provenance: Provenance


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    answer_id: str
    question_id: str
    scope: AnswerScope = "article"
    doc_ids: list[str] = Field(default_factory=list)
    value: str | None
    status: AnswerStatus
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)
    model: str | None = None
    prompt_version: str | None = None


class ArticleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    article: Article
    authors: list[Author] = Field(default_factory=list)
    authorships: list[Authorship] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
    chunks: list[Chunk] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    external_works: list[ExternalWork] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    answers: list[Answer] = Field(default_factory=list)
