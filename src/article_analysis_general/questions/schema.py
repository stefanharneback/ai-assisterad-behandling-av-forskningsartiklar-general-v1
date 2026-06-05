from __future__ import annotations

from article_analysis_general.store.record import Question


def validate_question_set(questions: list[Question]) -> list[Question]:
    ids = [question.question_id for question in questions]
    if len(ids) != len(set(ids)):
        raise ValueError("question_id values must be unique")
    return questions

