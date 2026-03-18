"""Practice engine for orchestrating interview practice sessions.

This module provides the core PracticeEngine class that coordinates
question selection, answer submission, feedback analysis, and progress tracking.

Contracts:
    - PracticeEngine: Orchestrates practice sessions
    - Integrates with QuestionBank, ProgressTracker, FeedbackAnalyzer (via protocols)
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Protocol

from ..models import PracticeMode
from ..models import PracticeSession
from ..models import QuestionAttempt
from ..models import QuestionCategory

if TYPE_CHECKING:
    pass


class QuestionBankProtocol(Protocol):
    """Protocol for QuestionBank dependency."""

    def get_questions(
        self,
        category: QuestionCategory | None = None,
        limit: int | None = None,
        exclude_ids: list[str] | None = None,
    ) -> list[dict]:
        """Get questions, optionally filtered."""
        ...

    def get_question_by_id(self, question_id: str) -> dict | None:
        """Get a specific question by ID."""
        ...


class ProgressTrackerProtocol(Protocol):
    """Protocol for ProgressTracker dependency."""

    def save_session(self, session: PracticeSession) -> None:
        """Save a completed session."""
        ...

    def get_weak_areas(self) -> list[str]:
        """Get identified weak areas from history."""
        ...

    def get_completed_question_ids(self) -> list[str]:
        """Get IDs of previously completed questions."""
        ...


class FeedbackAnalyzerProtocol(Protocol):
    """Protocol for FeedbackAnalyzer dependency."""

    async def analyze_answer(
        self,
        question: dict,
        answer: str,
    ) -> tuple[str, float, list[str]]:
        """Analyze an answer and return feedback, score, and weak areas."""
        ...


class ScorerProtocol(Protocol):
    """Protocol for Scorer dependency."""

    def calculate_score(
        self,
        question: dict,
        answer: str,
        feedback: str,
    ) -> float:
        """Calculate a score for the answer."""
        ...


class PracticeEngine:
    """Orchestrates practice sessions for interview preparation.

    This is the core engine that coordinates:
    - Question selection from QuestionBank
    - Answer submission and feedback
    - Progress tracking via ProgressTracker

    Example:
        >>> engine = PracticeEngine(
        ...     question_bank=bank,
        ...     progress_tracker=tracker,
        ...     feedback_analyzer=analyzer
        ... )
        >>> session = await engine.start_session(
        ...     mode=PracticeMode.focused,
        ...     category=QuestionCategory.behavioral
        ... )
        >>> attempt = await engine.get_next_question()
        >>> result = await engine.submit_answer(attempt.question_id, "My answer")
    """

    def __init__(
        self,
        question_bank: QuestionBankProtocol,
        progress_tracker: ProgressTrackerProtocol,
        feedback_analyzer: FeedbackAnalyzerProtocol,
        scorer: ScorerProtocol | None = None,
        hard_mode: bool = False,
    ):
        """Initialize the practice engine.

        Args:
            question_bank: Source of questions
            progress_tracker: Records progress
            feedback_analyzer: Analyzes answers for feedback
            scorer: Optional scorer for calculating scores
            hard_mode: Whether to use tougher scoring and feedback
        """
        self._question_bank = question_bank
        self._progress_tracker = progress_tracker
        self._feedback_analyzer = feedback_analyzer
        self._scorer = scorer
        self._hard_mode = hard_mode
        self._current_session: PracticeSession | None = None
        self._pending_questions: list[dict] = []

    async def start_session(
        self,
        mode: PracticeMode,
        category: QuestionCategory | None = None,
        time_limit: int | None = None,
        hard_mode: bool | None = None,
    ) -> PracticeSession:
        """Start a new practice session.

        Args:
            mode: Practice mode (focused, mixed, timed, review)
            category: Optional category filter for focused mode
            time_limit: Optional time limit in seconds for timed mode
            hard_mode: Optional override for hard mode (uses instance default if None)

        Returns:
            The newly created PracticeSession

        Raises:
            ValueError: If a session is already in progress
        """
        if self._current_session is not None:
            raise ValueError(
                "Session already in progress. Call end_session() first."
            )

        # Use provided hard_mode or fall back to instance default
        session_hard_mode = hard_mode if hard_mode is not None else self._hard_mode

        session_id = str(uuid.uuid4())
        self._current_session = PracticeSession(
            session_id=session_id,
            mode=mode,
            category_filter=category.value if category else None,
            time_limit_seconds=time_limit,
            hard_mode=session_hard_mode,
        )

        exclude_ids = self._progress_tracker.get_completed_question_ids()
        self._pending_questions = self._question_bank.get_questions(
            category=category,
            limit=self._get_question_limit(mode),
            exclude_ids=exclude_ids if mode != PracticeMode.review else None,
        )

        return self._current_session

    async def get_next_question(self) -> QuestionAttempt | None:
        """Get the next question to ask.

        Returns:
            QuestionAttempt with empty answer, or None if session complete.

        Raises:
            ValueError: If no session is in progress
        """
        if self._current_session is None:
            raise ValueError("No session in progress. Call start_session() first.")

        if not self._pending_questions:
            return None

        question = self._pending_questions.pop(0)

        return QuestionAttempt(
            question_id=question["id"],
            question_text=question["text"],
            category=QuestionCategory(question["category"]),
            user_answer="",
            scout_feedback="",
            score=0.0,
        )

    async def submit_answer(
        self,
        question_id: str,
        answer: str,
    ) -> QuestionAttempt:
        """Submit user's answer and get feedback.

        Args:
            question_id: ID of the question being answered
            answer: User's answer text

        Returns:
            QuestionAttempt with feedback, score, and weak areas populated

        Raises:
            ValueError: If no session is in progress or question not found
        """
        if self._current_session is None:
            raise ValueError("No session in progress. Call start_session() first.")

        question = self._question_bank.get_question_by_id(question_id)
        if question is None:
            raise ValueError(f"Question not found: {question_id}")

        hard_mode = self._current_session.hard_mode

        feedback, score, weak_areas = await self._feedback_analyzer.analyze_answer(
            question, answer, hard_mode=hard_mode
        )

        if self._scorer:
            score = self._scorer.calculate_score(question, answer, feedback, hard_mode=hard_mode)

        attempt = QuestionAttempt(
            question_id=question_id,
            question_text=question["text"],
            category=QuestionCategory(question["category"]),
            user_answer=answer,
            scout_feedback=feedback,
            score=score,
            weak_areas=weak_areas,
        )

        self._current_session.questions.append(attempt)
        return attempt

    async def end_session(self) -> PracticeSession:
        """End the current session and save progress.

        Returns:
            The completed PracticeSession

        Raises:
            ValueError: If no session is in progress
        """
        if self._current_session is None:
            raise ValueError("No session in progress. Call start_session() first.")

        self._current_session.completed_at = datetime.now()
        self._progress_tracker.save_session(self._current_session)

        completed = self._current_session
        self._current_session = None
        self._pending_questions = []

        return completed

    def get_current_session(self) -> PracticeSession | None:
        """Get the active practice session.

        Returns:
            Current session or None if no session active
        """
        return self._current_session

    def _get_question_limit(self, mode: PracticeMode) -> int:
        """Get the number of questions for a session based on mode."""
        limits = {
            PracticeMode.focused: 5,
            PracticeMode.mixed: 10,
            PracticeMode.timed: 15,
            PracticeMode.review: 5,
        }
        return limits.get(mode, 5)
