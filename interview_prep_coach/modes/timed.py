"""Timed practice mode with countdown pressure.

This module provides TimedMode for practicing under time constraints,
simulating real interview pressure.

Contracts:
    - TimedMode: Practice session with time limits per question
    - Enforces countdown and auto-skips on timeout
"""

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from ..models import PracticeMode
from ..models import PracticeSession

if TYPE_CHECKING:
    from ..practice.engine import PracticeEngine


class TimedMode:
    """Practice mode with time limits.

    Runs a practice session with countdown timers, simulating
    the pressure of real interviews. Tracks time per question.

    Example:
        >>> engine = PracticeEngine(bank, tracker, analyzer)
        >>> mode = TimedMode(engine, time_per_question=120)
        >>> session = await mode.run(num_questions=5)
        >>> session.time_limit_seconds
        600
    """

    DEFAULT_TIME_PER_QUESTION = 120

    def __init__(self, engine: "PracticeEngine", time_per_question: int = 120):
        """Initialize timed mode.

        Args:
            engine: PracticeEngine instance for running sessions
            time_per_question: Seconds allowed per question (default 120)
        """
        self._engine = engine
        self._time_per_question = time_per_question

    async def run(self, num_questions: int = 5) -> PracticeSession:
        """Run timed practice session.

        Args:
            num_questions: Number of questions to practice (default 5)

        Returns:
            Completed PracticeSession with time_limit_seconds set

        Raises:
            ValueError: If engine session setup fails
        """
        total_time = num_questions * self._time_per_question

        await self._engine.start_session(
            mode=PracticeMode.timed,
            time_limit=total_time,
        )

        start_time = datetime.now()

        for _ in range(num_questions):
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= total_time:
                break

            question = await self._engine.get_next_question()
            if question is None:
                break

            remaining_time = total_time - elapsed
            if remaining_time <= 0:
                break

        return await self._engine.end_session()

    @property
    def time_per_question(self) -> int:
        """Get seconds allowed per question."""
        return self._time_per_question

    async def _run_with_timer(
        self,
        question_handler,
        timeout_seconds: int,
    ) -> bool:
        """Run a question handler with timeout.

        Args:
            question_handler: Async function to handle the question
            timeout_seconds: Maximum seconds before timeout

        Returns:
            True if completed in time, False if timed out
        """
        try:
            await asyncio.wait_for(question_handler(), timeout=timeout_seconds)
            return True
        except TimeoutError:
            return False
