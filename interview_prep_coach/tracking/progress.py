"""Progress tracker for interview practice history.

This module provides the ProgressTracker class for persisting practice
data, calculating category scores, detecting weak areas, and providing
progress summaries.

Contracts:
    - ProgressTracker: Persists and analyzes practice history
    - Implements ProgressTrackerProtocol from engine.py
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from ..models import PracticeSession
from ..models import ProgressSummary
from ..models import QuestionAttempt


class ProgressTracker:
    """Tracks and persists interview practice progress.

    Stores practice history in JSON files, calculates category scores,
    detects weak areas from patterns, and provides progress summaries.

    Example:
        >>> tracker = ProgressTracker(data_dir=Path("./data"))
        >>> tracker.record_attempt(attempt)
        >>> summary = tracker.get_summary()
        >>> weak = tracker.get_weak_areas(threshold=3)
    """

    def __init__(self, data_dir: Path | None = None):
        """Initialize with optional data directory for persistence.

        Args:
            data_dir: Directory for storing JSON data files.
                     Defaults to ./data/tracking if not specified.
        """
        self._data_dir = data_dir or Path("./data/tracking")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._sessions_file = self._data_dir / "sessions.json"
        self._attempts_file = self._data_dir / "attempts.json"
        self._sessions: list[PracticeSession] = []
        self._attempts: list[QuestionAttempt] = []
        self._load_data()

    def _load_data(self) -> None:
        """Load persisted data from JSON files."""
        if self._sessions_file.exists():
            with open(self._sessions_file) as f:
                data = json.load(f)
                self._sessions = [
                    PracticeSession(**s) for s in data.get("sessions", [])
                ]

        if self._attempts_file.exists():
            with open(self._attempts_file) as f:
                data = json.load(f)
                self._attempts = [
                    self._deserialize_attempt(a) for a in data.get("attempts", [])
                ]

    def _deserialize_attempt(self, data: dict) -> QuestionAttempt:
        """Deserialize attempt dict, handling datetime conversion."""
        if isinstance(data.get("attempted_at"), str):
            data["attempted_at"] = datetime.fromisoformat(data["attempted_at"])
        return QuestionAttempt(**data)

    def _save_sessions(self) -> None:
        """Persist sessions to JSON file."""
        with open(self._sessions_file, "w") as f:
            json.dump(
                {"sessions": [s.model_dump(mode="json") for s in self._sessions]},
                f,
                default=str,
                indent=2,
            )

    def _save_attempts(self) -> None:
        """Persist attempts to JSON file."""
        with open(self._attempts_file, "w") as f:
            json.dump(
                {"attempts": [a.model_dump(mode="json") for a in self._attempts]},
                f,
                default=str,
                indent=2,
            )

    def record_attempt(self, attempt: QuestionAttempt) -> None:
        """Record a question attempt.

        Args:
            attempt: The question attempt to record.
        """
        self._attempts.append(attempt)
        self._save_attempts()

    def get_summary(self) -> ProgressSummary:
        """Get a summary of all practice progress.

        Returns:
            ProgressSummary with total sessions, questions, avg score, etc.
        """
        total_sessions = len(self._sessions)
        total_questions = len(self._attempts)

        if total_questions == 0:
            return ProgressSummary()

        scores = [a.score for a in self._attempts]
        avg_score = sum(scores) / len(scores)

        category_scores = self.get_category_scores()
        weak_areas = self.get_weak_areas()
        improvement_trend = self._calculate_trend()

        return ProgressSummary(
            total_sessions=total_sessions,
            total_questions_practiced=total_questions,
            avg_score=round(avg_score, 2),
            category_scores=category_scores,
            weak_areas=weak_areas,
            improvement_trend=improvement_trend,
        )

    def _calculate_trend(self) -> str:
        """Calculate improvement trend from recent attempts."""
        if len(self._attempts) < 4:
            return "stable"

        sorted_attempts = sorted(self._attempts, key=lambda a: a.attempted_at)
        mid = len(sorted_attempts) // 2
        first_half_avg = sum(a.score for a in sorted_attempts[:mid]) / mid
        second_half_avg = sum(a.score for a in sorted_attempts[mid:]) / (
            len(sorted_attempts) - mid
        )

        diff = second_half_avg - first_half_avg
        if diff > 0.5:
            return "improving"
        elif diff < -0.5:
            return "declining"
        return "stable"

    def get_weak_areas(self, threshold: int = 3) -> list[str]:
        """Get weak areas that appear frequently.

        Args:
            threshold: Minimum number of occurrences to be considered weak.

        Returns:
            List of weak areas sorted by frequency.
        """
        low_score_attempts = [a for a in self._attempts if a.score < 7.0]

        area_counter: Counter[str] = Counter()
        for attempt in low_score_attempts:
            for area in attempt.weak_areas:
                area_counter[area] += 1

        return [area for area, count in area_counter.most_common() if count >= threshold]

    def get_category_scores(self) -> dict[str, float]:
        """Get average scores by category.

        Returns:
            Dict mapping category name to average score.
        """
        category_scores: dict[str, list[float]] = {}

        for attempt in self._attempts:
            cat = attempt.category.value
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(attempt.score)

        return {
            cat: round(sum(scores) / len(scores), 2)
            for cat, scores in category_scores.items()
        }

    def save_session(self, session: PracticeSession) -> None:
        """Save a completed practice session.

        Args:
            session: The practice session to save.
        """
        for attempt in session.questions:
            if attempt not in self._attempts:
                self._attempts.append(attempt)

        self._sessions.append(session)
        self._save_sessions()
        self._save_attempts()

    def get_sessions(self) -> list[PracticeSession]:
        """Get all saved practice sessions.

        Returns:
            List of all practice sessions.
        """
        return self._sessions.copy()

    def get_completed_question_ids(self) -> list[str]:
        """Get IDs of previously completed questions.

        Returns:
            List of question IDs that have been attempted.
        """
        return list({a.question_id for a in self._attempts})
