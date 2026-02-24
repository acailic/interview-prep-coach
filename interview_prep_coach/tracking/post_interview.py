"""Post-interview capture for logging real interview experiences.

This module provides the PostInterviewCapture class for recording
real interview data, extracting learnings, and feeding questions back
into the practice system.

Contracts:
    - PostInterviewCapture: Captures and persists post-interview data
    - Integrates with QuestionBank to add interview questions
    - Aggregates learnings across all logged interviews
"""

from collections import Counter
from datetime import date
from datetime import datetime
from datetime import timezone
from pathlib import Path

UTC = timezone.utc

from ..models import InterviewOutcome
from ..models import PostInterviewLog


class PostInterviewCapture:
    """Captures data from real interviews and feeds back into practice.

    Responsibilities:
    - Logs completed interviews with questions asked
    - Adds interview questions to the question bank
    - Tracks strengths and weaknesses over time
    - Analyzes outcome patterns for insights

    Example:
        >>> from interview_prep.practice import QuestionBank
        >>> bank = QuestionBank()
        >>> capture = PostInterviewCapture(question_bank=bank)
        >>> log = capture.log_interview(
        ...     company="TechCorp",
        ...     position="Senior Engineer",
        ...     questions_asked=["Tell me about yourself", "Design a cache"],
        ...     what_went_well=["Clear communication"],
        ...     what_stumped=["Distributed locking"],
        ... )
        >>> learnings = capture.get_learnings()
    """

    def __init__(
        self,
        progress_tracker=None,
        question_bank=None,
        data_dir: Path | None = None,
    ):
        """Initialize with optional dependencies and data directory.

        Args:
            progress_tracker: Optional ProgressTracker for integration
            question_bank: Optional QuestionBank for adding interview questions
            data_dir: Directory for storing JSON data files.
                     Defaults to ./data/tracking if not specified.
        """
        self._progress_tracker = progress_tracker
        self._question_bank = question_bank
        self._data_dir = data_dir or Path("./data/tracking")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._interviews_file = self._data_dir / "post_interviews.json"
        self._interviews: list[PostInterviewLog] = []
        self._load_data()

    def _load_data(self) -> None:
        """Load persisted interviews from JSON file."""
        if self._interviews_file.exists():
            import json

            with open(self._interviews_file) as f:
                data = json.load(f)
                self._interviews = [
                    self._deserialize_interview(i) for i in data.get("interviews", [])
                ]

    def _deserialize_interview(self, data: dict) -> PostInterviewLog:
        """Deserialize interview dict, handling date conversion."""
        if isinstance(data.get("interview_date"), str):
            data["interview_date"] = date.fromisoformat(data["interview_date"])
        if isinstance(data.get("outcome"), str):
            data["outcome"] = InterviewOutcome(data["outcome"])
        return PostInterviewLog(**data)

    def _save_interviews(self) -> None:
        """Persist interviews to JSON file."""
        import json

        with open(self._interviews_file, "w") as f:
            json.dump(
                {"interviews": [i.model_dump(mode="json") for i in self._interviews]},
                f,
                default=str,
                indent=2,
            )

    def log_interview(
        self,
        company: str,
        position: str,
        questions_asked: list[str],
        what_went_well: list[str],
        what_stumped: list[str],
        style_notes: str | None = None,
        outcome: InterviewOutcome | None = None,
    ) -> PostInterviewLog:
        """Log a completed interview.

        Args:
            company: Company name
            position: Position title
            questions_asked: Questions the interviewer asked
            what_went_well: What the candidate did well
            what_stumped: What the candidate struggled with
            style_notes: Notes about interview style/format
            outcome: Interview outcome (pending, offer, rejected, withdrawn)

        Returns:
            The created PostInterviewLog.
        """
        log = PostInterviewLog(
            interview_date=datetime.now(tz=UTC).date(),
            company=company,
            position=position,
            questions_asked=questions_asked,
            what_went_well=what_went_well,
            what_stumped=what_stumped,
            style_notes=style_notes,
            outcome=outcome,
        )

        self._interviews.append(log)
        self._save_interviews()

        if self._question_bank and questions_asked:
            self._question_bank.add_from_interview(questions_asked)

        return log

    def get_learnings(self) -> dict:
        """Get aggregated learnings from all logged interviews.

        Returns:
            {
                "common_questions": [...],  # Questions asked frequently
                "strengths": [...],  # Recurring strengths
                "weaknesses": [...],  # Recurring weaknesses
                "outcome_patterns": {...},  # Success/failure patterns
            }
        """
        if not self._interviews:
            return {
                "common_questions": [],
                "strengths": [],
                "weaknesses": [],
                "outcome_patterns": {},
            }

        question_counter: Counter[str] = Counter()
        strength_counter: Counter[str] = Counter()
        weakness_counter: Counter[str] = Counter()
        outcome_by_company: dict[str, list[InterviewOutcome]] = {}

        for interview in self._interviews:
            for q in interview.questions_asked:
                question_counter[q] += 1
            for s in interview.what_went_well:
                strength_counter[s] += 1
            for w in interview.what_stumped:
                weakness_counter[w] += 1
            if interview.outcome:
                if interview.company not in outcome_by_company:
                    outcome_by_company[interview.company] = []
                outcome_by_company[interview.company].append(interview.outcome)

        common_questions = [q for q, count in question_counter.most_common(10) if count >= 2]
        strengths = [s for s, count in strength_counter.most_common(10) if count >= 2]
        weaknesses = [w for w, count in weakness_counter.most_common(10) if count >= 2]

        outcome_patterns = self._analyze_outcome_patterns()

        return {
            "common_questions": common_questions,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "outcome_patterns": outcome_patterns,
        }

    def _analyze_outcome_patterns(self) -> dict:
        """Analyze patterns in interview outcomes.

        Returns:
            {
                "total_interviews": int,
                "by_outcome": {"offer": N, "rejected": N, ...},
                "offer_rate": float,
            }
        """
        if not self._interviews:
            return {
                "total_interviews": 0,
                "by_outcome": {},
                "offer_rate": 0.0,
            }

        outcome_counter: Counter[str] = Counter()
        for interview in self._interviews:
            if interview.outcome:
                outcome_counter[interview.outcome.value] += 1

        total = len(self._interviews)
        offers = outcome_counter.get(InterviewOutcome.offer.value, 0)
        offer_rate = offers / total if total > 0 else 0.0

        return {
            "total_interviews": total,
            "by_outcome": dict(outcome_counter),
            "offer_rate": round(offer_rate, 2),
        }

    def get_interviews(self) -> list[PostInterviewLog]:
        """Get all logged interviews.

        Returns:
            List of all PostInterviewLog entries.
        """
        return self._interviews.copy()

    def get_by_company(self, company: str) -> list[PostInterviewLog]:
        """Get interviews for a specific company.

        Args:
            company: Company name to filter by

        Returns:
            List of interviews at that company.
        """
        return [i for i in self._interviews if i.company.lower() == company.lower()]

    def get_by_outcome(self, outcome: InterviewOutcome) -> list[PostInterviewLog]:
        """Get interviews with a specific outcome.

        Args:
            outcome: Outcome to filter by

        Returns:
            List of interviews with that outcome.
        """
        return [i for i in self._interviews if i.outcome == outcome]

    def update_outcome(self, company: str, position: str, outcome: InterviewOutcome) -> bool:
        """Update the outcome of a previously logged interview.

        Args:
            company: Company name
            position: Position title
            outcome: New outcome

        Returns:
            True if interview was found and updated, False otherwise.
        """
        for interview in self._interviews:
            if (
                interview.company.lower() == company.lower()
                and interview.position.lower() == position.lower()
                and interview.outcome in (None, InterviewOutcome.pending)
            ):
                interview.outcome = outcome
                self._save_interviews()
                return True
        return False
