from __future__ import annotations

import unittest

from article_analysis_general.store.record import Article, ArticleSource, Author, Authorship, Evidence, Provenance, Question, Section


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


if __name__ == "__main__":
    unittest.main()
