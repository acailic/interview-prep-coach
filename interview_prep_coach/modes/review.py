"""Review mode for practicing weak areas.

This module provides ReviewMode for focused practice on identified
weak spots from practice history.

Contracts:
    - ReviewMode: Practice session focusing on weak areas
    - Uses ProgressTracker to identify weak areas
    - Prioritizes questions related to weak areas
"""

from typing import TYPE_CHECKING

from ..models import PracticeMode
from ..models import PracticeSession

if TYPE_CHECKING:
    from ..practice.engine import PracticeEngine
    from ..tracking.progress import ProgressTracker


class ReviewMode:
    """Practice mode focusing on weak areas.

    Analyzes practice history to identify weak areas and
    prioritizes questions that target those areas.

    Example:
        >>> engine = PracticeEngine(bank, tracker, analyzer)
        >>> mode = ReviewMode(engine, tracker)
        >>> session = await mode.run(num_questions=5)
        >>> len(session.questions) > 0
        True
    """

    def __init__(
        self,
        engine: "PracticeEngine",
        progress_tracker: "ProgressTracker",
    ):
        """Initialize review mode.

        Args:
            engine: PracticeEngine instance for running sessions
            progress_tracker: ProgressTracker for identifying weak areas
        """
        self._engine = engine
        self._progress_tracker = progress_tracker

    async def run(self, num_questions: int = 5) -> PracticeSession:
        """Run review session on weak areas.

        Args:
            num_questions: Number of questions to practice (default 5)

        Returns:
            Completed PracticeSession focused on weak areas

        Raises:
            ValueError: If engine session setup fails
        """
        self._progress_tracker.get_weak_areas(threshold=2)

        await self._engine.start_session(
            mode=PracticeMode.review,
        )

        for _ in range(num_questions):
            question = await self._engine.get_next_question()
            if question is None:
                break

        return await self._engine.end_session()

    def get_weak_areas(self) -> list[str]:
        """Get currently identified weak areas.

        Returns:
            List of weak area identifiers
        """
        return self._progress_tracker.get_weak_areas()

    def get_weak_category(self) -> str | None:
        """Get the category with lowest average score.

        Returns:
            Category name with lowest score, or None if no data
        """
        scores = self._progress_tracker.get_category_scores()
        if not scores:
            return None

        return min(scores, key=scores.get)
