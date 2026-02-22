"""Interview day preparation modes.

This module provides InterviewDayMode for quick prep sessions
on the night before or morning of an interview.

Contracts:
    - InterviewDayMode: Quick review modes for interview day
    - night_before: Comprehensive review session
    - morning_of: 5-minute warmup
    - one_hour_before: Final prep
"""

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..tracking.progress import ProgressTracker


class SessionManager:
    """Manages session creation for interview day modes."""

    def __init__(self, progress_tracker: "ProgressTracker"):
        self._progress_tracker = progress_tracker

    def create_quick_session(self, focus_areas: list[str] | None = None) -> dict:
        """Create a quick review session configuration."""
        return {
            "focus_areas": focus_areas or [],
            "created_at": datetime.now().isoformat(),
        }


class InterviewDayMode:
    """Special modes for interview day preparation.

    Provides targeted quick review sessions for:
    - Night before: Comprehensive review of all weak areas
    - Morning of: 5-minute warmup with key talking points
    - 1 hour before: Final confidence boost

    Example:
        >>> mode = InterviewDayMode(session_manager, tracker)
        >>> review = await mode.night_before()
        >>> print(review[:50])
        'Night Before Interview Review\\n============================...'
    """

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        progress_tracker: "ProgressTracker | None" = None,
    ):
        """Initialize interview day mode.

        Args:
            session_manager: Optional session manager for creating sessions
            progress_tracker: ProgressTracker for identifying focus areas
        """
        self._session_manager = session_manager
        self._progress_tracker = progress_tracker

    async def night_before(self) -> str:
        """Quick review for night before interview.

        Generates a comprehensive review covering:
        - Top weak areas to focus on
        - Key talking points from practice history
        - Questions you struggled with most

        Returns:
            Formatted review string for night-before study
        """
        lines = ["Night Before Interview Review", "=" * 30, ""]

        if self._progress_tracker:
            weak_areas = self._progress_tracker.get_weak_areas(threshold=2)
            if weak_areas:
                lines.append("Focus Areas to Review:")
                for i, area in enumerate(weak_areas[:5], 1):
                    lines.append(f"  {i}. {area}")
                lines.append("")

            category_scores = self._progress_tracker.get_category_scores()
            if category_scores:
                lines.append("Category Performance:")
                for cat, score in sorted(
                    category_scores.items(), key=lambda x: x[1]
                ):
                    status = "OK" if score >= 7.0 else "NEEDS WORK"
                    lines.append(f"  - {cat}: {score:.1f} [{status}]")
                lines.append("")

            summary = self._progress_tracker.get_summary()
            lines.append(f"Total practice sessions: {summary.total_sessions}")
            lines.append(f"Questions practiced: {summary.total_questions_practiced}")
            lines.append(f"Average score: {summary.avg_score:.1f}")
            lines.append(f"Trend: {summary.improvement_trend}")

        lines.append("")
        lines.append("Reminders for tomorrow:")
        lines.append("  - Get good sleep")
        lines.append("  - Review STAR stories")
        lines.append("  - Prepare questions to ask")
        lines.append("  - You've got this!")

        return "\n".join(lines)

    async def morning_of(self) -> str:
        """5-minute warmup for morning of interview.

        Generates a quick warmup covering:
        - 2-3 key talking points
        - Quick confidence reminder
        - Breathing exercise prompt

        Returns:
            Formatted 5-minute warmup string
        """
        lines = ["Morning Warmup (5 minutes)", "=" * 25, ""]

        if self._progress_tracker:
            summary = self._progress_tracker.get_summary()
            lines.append(f"You've completed {summary.total_sessions} practice sessions!")
            lines.append(f"Average score: {summary.avg_score:.1f}")
            lines.append("")

            weak_areas = self._progress_tracker.get_weak_areas(threshold=3)
            if weak_areas:
                lines.append("Quick reminder - watch for:")
                for area in weak_areas[:3]:
                    lines.append(f"  - {area}")
                lines.append("")

        lines.append("Quick confidence boost:")
        lines.append("  1. Take 3 deep breaths")
        lines.append("  2. Remember: You are prepared")
        lines.append("  3. Smile - you've got this!")
        lines.append("")
        lines.append("Key talking points to remember:")
        lines.append("  - Your biggest achievement")
        lines.append("  - A challenge you overcame")
        lines.append("  - Why you're excited about this role")

        return "\n".join(lines)

    async def one_hour_before(self) -> str:
        """Final prep 1 hour before.

        Generates final prep checklist:
        - Last-minute reminders
        - Questions to ask interviewer
        - Technical quick review

        Returns:
            Formatted final prep string
        """
        lines = ["Final Prep - 1 Hour Before", "=" * 25, ""]

        lines.append("CHECKLIST:")
        lines.append("  [ ] Test your audio/video setup")
        lines.append("  [ ] Have water nearby")
        lines.append("  [ ] Close unnecessary tabs/apps")
        lines.append("  [ ] Have your resume/notes ready")
        lines.append("  [ ] Silence your phone")
        lines.append("")

        if self._progress_tracker:
            weak_areas = self._progress_tracker.get_weak_areas(threshold=2)
            if weak_areas:
                lines.append("Quick review (last weak areas):")
                for area in weak_areas[:2]:
                    lines.append(f"  - {area}")
                lines.append("")

        lines.append("Questions to ask them:")
        lines.append("  1. What does success look like in this role?")
        lines.append("  2. What's the biggest challenge the team is facing?")
        lines.append("  3. How would you describe the team culture?")
        lines.append("")

        lines.append("STAR Method Reminder:")
        lines.append("  S - Situation (context)")
        lines.append("  T - Task (what you needed to do)")
        lines.append("  A - Action (what YOU did)")
        lines.append("  R - Result (outcome, with metrics)")
        lines.append("")
        lines.append("You are ready. Good luck!")

        return "\n".join(lines)

    def get_mode(self, timing: str) -> str:
        """Get suggested mode based on timing.

        Args:
            timing: One of 'night_before', 'morning_of', 'one_hour_before'

        Returns:
            Description of which method to call
        """
        modes = {
            "night_before": "Run night_before() for comprehensive review",
            "morning_of": "Run morning_of() for 5-minute warmup",
            "one_hour_before": "Run one_hour_before() for final checklist",
        }
        return modes.get(timing, "Unknown timing. Use night_before, morning_of, or one_hour_before")
