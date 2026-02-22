"""Focused practice mode for category-specific practice.

This module provides FocusedMode for practicing questions from a single
category with detailed feedback and repeated practice on weak spots.

Contracts:
    - FocusedMode: Practice session focused on one category
    - Returns PracticeSession with category_filter set
"""

from typing import TYPE_CHECKING

from ..models import PracticeMode
from ..models import PracticeSession
from ..models import QuestionCategory

if TYPE_CHECKING:
    from ..practice.engine import PracticeEngine


class FocusedMode:
    """Practice mode focused on a specific category.

    Runs a practice session with questions only from the selected
    category. Useful for targeted improvement in one area.

    Example:
        >>> engine = PracticeEngine(bank, tracker, analyzer)
        >>> mode = FocusedMode(engine, QuestionCategory.behavioral)
        >>> session = await mode.run(num_questions=5)
        >>> session.category_filter
        'behavioral'
    """

    def __init__(self, engine: "PracticeEngine", category: QuestionCategory):
        """Initialize focused mode.

        Args:
            engine: PracticeEngine instance for running sessions
            category: The category to focus on
        """
        self._engine = engine
        self._category = category

    async def run(self, num_questions: int = 5) -> PracticeSession:
        """Run focused practice session.

        Args:
            num_questions: Number of questions to practice (default 5)

        Returns:
            Completed PracticeSession with category_filter set

        Raises:
            ValueError: If engine session setup fails
        """
        await self._engine.start_session(
            mode=PracticeMode.focused,
            category=self._category,
        )

        for _ in range(num_questions):
            question = await self._engine.get_next_question()
            if question is None:
                break

        return await self._engine.end_session()

    @property
    def category(self) -> QuestionCategory:
        """Get the focused category."""
        return self._category
