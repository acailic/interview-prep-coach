"""Question bank for managing practice questions.

This module provides the QuestionBank class that manages the pool of
practice questions from prep guides and custom additions.

Contracts:
    - Implements QuestionBankProtocol from engine.py
    - Loads questions from PrepGuide.practice_questions
    - Stores custom questions added by user
    - Filters by category and excludes IDs
"""

import uuid
from typing import Any

from ..models import PracticeQuestion
from ..models import PrepGuide
from ..models import QuestionCategory


class QuestionBank:
    """Manages the pool of practice questions.

    Questions come from:
    1. PrepGuide.practice_questions (loaded via load_from_profile)
    2. Custom questions added via add_question
    3. Post-interview questions (added as custom)

    Example:
        >>> bank = QuestionBank()
        >>> bank.load_from_profile(prep_guide)
        10
        >>> questions = bank.get_questions(category=QuestionCategory.behavioral)
        >>> len(questions)
        3
        >>> custom = bank.add_question("Why this company?", QuestionCategory.behavioral)
        >>> bank.get_question_by_id(custom["id"])
        {'id': '...', 'text': 'Why this company?', ...}
    """

    def __init__(self) -> None:
        """Initialize empty question bank."""
        self._questions: list[dict[str, Any]] = []

    def get_questions(
        self,
        category: QuestionCategory | None = None,
        limit: int | None = None,
        exclude_ids: list[str] | None = None,
    ) -> list[dict]:
        """Get questions, optionally filtered by category.

        Args:
            category: Filter by question category (behavioral, technical, etc.)
            limit: Maximum number of questions to return
            exclude_ids: Question IDs to exclude (e.g., already asked)

        Returns:
            List of question dicts with 'id', 'text', 'category', etc.
        """
        exclude_set = set(exclude_ids) if exclude_ids else set()

        result = []
        for q in self._questions:
            if q["id"] in exclude_set:
                continue
            if category is not None and q["category"] != category.value:
                continue
            result.append(q)

        if limit is not None and limit > 0:
            result = result[:limit]

        return result

    def get_question_by_id(self, question_id: str) -> dict | None:
        """Get a specific question by ID.

        Args:
            question_id: The unique identifier of the question

        Returns:
            Question dict or None if not found
        """
        for q in self._questions:
            if q["id"] == question_id:
                return q
        return None

    def add_question(
        self,
        question: str,
        category: QuestionCategory,
        notes: str | None = None,
        difficulty: str = "medium",
    ) -> dict:
        """Add a custom question to the bank.

        Args:
            question: The question text
            category: Question category
            notes: Optional notes/hints for the question
            difficulty: Difficulty level (easy, medium, hard)

        Returns:
            The created question dict with generated ID
        """
        q_id = str(uuid.uuid4())
        q_dict: dict[str, Any] = {
            "id": q_id,
            "text": question,
            "category": category.value,
            "difficulty": difficulty,
            "notes": notes,
            "source": "custom",
        }
        self._questions.append(q_dict)
        return q_dict

    def get_unpracticed(self, practiced_ids: list[str]) -> list[dict]:
        """Get questions not yet practiced.

        Args:
            practiced_ids: IDs of questions already practiced

        Returns:
            List of questions not in practiced_ids
        """
        practiced_set = set(practiced_ids)
        return [q for q in self._questions if q["id"] not in practiced_set]

    def load_from_profile(self, prep_guide: PrepGuide) -> int:
        """Load questions from the generated prep guide.

        Args:
            prep_guide: PrepGuide model with practice_questions

        Returns:
            Number of questions loaded
        """
        loaded = 0
        for pq in prep_guide.practice_questions:
            q_id = str(uuid.uuid4())
            category = self._normalize_category(pq.category)
            q_dict: dict[str, Any] = {
                "id": q_id,
                "text": pq.question,
                "category": category,
                "difficulty": pq.difficulty,
                "notes": pq.notes,
                "source": "prep_guide",
            }
            if not self._question_exists(pq.question):
                self._questions.append(q_dict)
                loaded += 1

        return loaded

    def add_from_interview(
        self,
        questions: list[str],
        category: QuestionCategory = QuestionCategory.behavioral,
    ) -> int:
        """Add questions captured from a real interview.

        Args:
            questions: List of questions asked in the interview
            category: Default category for these questions

        Returns:
            Number of questions added
        """
        added = 0
        for q_text in questions:
            if not self._question_exists(q_text):
                self.add_question(
                    question=q_text,
                    category=category,
                    notes="From real interview",
                    difficulty="medium",
                )
                added += 1
        return added

    def clear(self) -> None:
        """Remove all questions from the bank."""
        self._questions.clear()

    def count(self) -> int:
        """Return total number of questions in the bank."""
        return len(self._questions)

    def count_by_category(self) -> dict[str, int]:
        """Return count of questions per category."""
        counts: dict[str, int] = {}
        for q in self._questions:
            cat = q["category"]
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _normalize_category(self, category: str) -> str:
        """Normalize category string to valid QuestionCategory value."""
        category_lower = category.lower().replace("-", "_").replace(" ", "_")

        category_map = {
            "behavioral": QuestionCategory.behavioral.value,
            "technical": QuestionCategory.technical.value,
            "system_design": QuestionCategory.system_design.value,
            "systemdesign": QuestionCategory.system_design.value,
            "coding": QuestionCategory.coding.value,
        }

        return category_map.get(category_lower, QuestionCategory.behavioral.value)

    def _question_exists(self, question_text: str) -> bool:
        """Check if a question with the same text already exists."""
        normalized = question_text.strip().lower()
        for q in self._questions:
            if q["text"].strip().lower() == normalized:
                return True
        return False
