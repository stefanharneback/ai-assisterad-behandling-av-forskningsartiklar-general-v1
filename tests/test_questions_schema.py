from __future__ import annotations

import unittest

from article_analysis_general.questions.schema import validate_question_set
from article_analysis_general.store.record import Question


class QuestionSchemaTests(unittest.TestCase):
    def test_validate_question_set_accepts_unique_question_ids(self) -> None:
        questions = [
            Question(question_id="q1", text="One?", method="sql", answer_schema="scalar"),
            Question(question_id="q2", text="Two?", method="long-context", answer_schema="evidence_text"),
        ]

        self.assertEqual(validate_question_set(questions), questions)

    def test_validate_question_set_rejects_duplicate_question_ids(self) -> None:
        questions = [
            Question(question_id="q1", text="One?", method="sql", answer_schema="scalar"),
            Question(question_id="q1", text="Duplicate?", method="rag", answer_schema="evidence_text"),
        ]

        with self.assertRaisesRegex(ValueError, "question_id"):
            validate_question_set(questions)


if __name__ == "__main__":
    unittest.main()
