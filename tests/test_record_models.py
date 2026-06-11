from __future__ import annotations

import unittest

from pydantic import ValidationError

from article_analysis_general.store.record import (
    Answer,
    AnswerSet,
    Article,
    ArticleRecord,
    ArticleSource,
    Author,
    Authorship,
    Evidence,
    PageRecord,
    Provenance,
    Question,
    Section,
)


class RecordModelTests(unittest.TestCase):
    def test_article_accepts_content_hash_doc_id(self) -> None:
        digest = "a" * 64
        article = Article(
            doc_id=digest,
            file_hash=digest,
            sources=[
                ArticleSource(
                    file_name="paper.pdf",
                    relative_path="SCOPUS/paper.pdf",
                    source_database="SCOPUS",
                )
            ],
        )

        self.assertEqual(article.doc_id, digest)
        self.assertEqual(article.extraction_status, "not_started")
        self.assertEqual(article.text_layer, "unknown")
        self.assertEqual(article.sources[0].source_database, "SCOPUS")

    def test_section_and_evidence_keep_provenance(self) -> None:
        section = Section(
            section_id="s1",
            doc_id="doc",
            heading="Methods",
            normalized_type="method",
            text="Methods text",
            provenance=Provenance(page_start=3, page_end=5, start_offset=0, end_offset=12),
        )
        evidence = Evidence(
            evidence_id="e1",
            doc_id="doc",
            quote="Methods text",
            provenance=Provenance(page=3, section_id=section.section_id, start_offset=0, end_offset=12),
        )

        self.assertEqual(section.normalized_type, "method")
        self.assertEqual(section.provenance.page_start, 3)
        self.assertEqual(evidence.provenance.section_id, "s1")

    def test_question_method_is_explicit_data(self) -> None:
        question = Question(
            question_id="q-purpose",
            text="What is the study purpose?",
            method="long-context",
            answer_schema="short_text_with_evidence",
        )

        self.assertEqual(question.method, "long-context")

    def test_author_and_authorship_are_first_class_records(self) -> None:
        author = Author(author_id="openalex:A123", display_name="Ada Example", openalex_id="https://openalex.org/A123")
        authorship = Authorship(work_id="article:doc", author_id=author.author_id, role="article", position=1)

        self.assertEqual(author.author_id, authorship.author_id)
        self.assertEqual(authorship.role, "article")

    def test_answer_can_target_one_article_or_a_corpus_scope(self) -> None:
        article_answer = Answer(
            answer_id="a1",
            question_id="q-summary",
            scope="article",
            doc_ids=["doc-1"],
            value="Short article summary.",
            status="found",
        )
        corpus_answer = Answer(
            answer_id="a2",
            question_id="q-network",
            scope="corpus",
            doc_ids=["doc-1", "doc-2"],
            value="Two articles share a reference.",
            status="found",
        )

        self.assertEqual(article_answer.doc_ids, ["doc-1"])
        self.assertEqual(corpus_answer.scope, "corpus")
        self.assertEqual(corpus_answer.doc_ids, ["doc-1", "doc-2"])

    def test_article_record_keeps_full_text_and_page_map_without_answers(self) -> None:
        article = Article(
            doc_id="doc",
            file_hash="doc",
            sources=[ArticleSource(file_name="paper.pdf", relative_path="SCOPUS/paper.pdf")],
        )
        record = ArticleRecord(
            article=article,
            full_text="Page one.\n\nPage two.",
            pages=[
                PageRecord(page_number=1, text="Page one.", start_offset=0, end_offset=9),
                PageRecord(page_number=2, text="Page two.", start_offset=11, end_offset=20),
            ],
        )

        self.assertEqual(record.full_text[record.pages[1].start_offset : record.pages[1].end_offset], "Page two.")
        with self.assertRaises(ValidationError):
            ArticleRecord.model_validate(
                {
                    "article": article.model_dump(),
                    "answers": [
                        {
                            "answer_id": "a1",
                            "question_id": "q1",
                            "value": "answer",
                            "status": "found",
                        }
                    ],
                }
            )

    def test_answer_set_is_run_scoped_output(self) -> None:
        question = Question(question_id="q1", text="Purpose?", method="long-context", answer_schema="text")
        evidence = Evidence(
            evidence_id="e1",
            doc_id="doc",
            quote="Purpose text",
            provenance=Provenance(page=1, start_offset=0, end_offset=12),
        )
        answer = Answer(
            answer_id="a1",
            question_id=question.question_id,
            doc_ids=["doc"],
            value="Purpose text",
            status="found",
            evidence_ids=[evidence.evidence_id],
        )

        answer_set = AnswerSet(run_id="run-1", questions=[question], evidence=[evidence], answers=[answer])

        self.assertEqual(answer_set.run_id, "run-1")
        self.assertEqual(answer_set.answers[0].evidence_ids, ["e1"])


if __name__ == "__main__":
    unittest.main()
