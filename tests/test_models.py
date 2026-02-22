"""Tests for data models."""

import pytest
from datetime import datetime

from interview_prep_coach.models import (
    PracticeMode,
    QuestionCategory,
    InterviewOutcome,
    QuestionAttempt,
    PracticeSession,
    ProgressSummary,
    PostInterviewLog,
)


class TestEnums:
    """Test enum values."""

    def test_practice_mode_values(self):
        assert PracticeMode.focused.value == "focused"
        assert PracticeMode.mixed.value == "mixed"
        assert PracticeMode.timed.value == "timed"
        assert PracticeMode.review.value == "review"

    def test_question_category_values(self):
        assert QuestionCategory.behavioral.value == "behavioral"
        assert QuestionCategory.technical.value == "technical"
        assert QuestionCategory.system_design.value == "system_design"
        assert QuestionCategory.coding.value == "coding"

    def test_interview_outcome_values(self):
        assert InterviewOutcome.pending.value == "pending"
        assert InterviewOutcome.offer.value == "offer"
        assert InterviewOutcome.rejected.value == "rejected"
        assert InterviewOutcome.withdrawn.value == "withdrawn"


class TestQuestionAttempt:
    """Test QuestionAttempt model."""

    def test_create_attempt(self):
        attempt = QuestionAttempt(
            question_id="test-123",
            question_text="Tell me about yourself",
            category=QuestionCategory.behavioral,
            user_answer="I am a software engineer...",
            scout_feedback="Good introduction, consider adding more specifics",
            score=7.5,
            weak_areas=["specificity"],
            attempted_at=datetime.now(),
        )
        assert attempt.question_id == "test-123"
        assert attempt.score == 7.5
        assert "specificity" in attempt.weak_areas

    def test_score_validation(self):
        with pytest.raises(ValueError):
            QuestionAttempt(
                question_id="test-123",
                question_text="Test question",
                category=QuestionCategory.behavioral,
                user_answer="Test answer",
                scout_feedback="Test feedback",
                score=11.0,  # Invalid: > 10
                weak_areas=[],
                attempted_at=datetime.now(),
            )


class TestPracticeSession:
    """Test PracticeSession model."""

    def test_create_session(self):
        session = PracticeSession(
            session_id="session-123",
            mode=PracticeMode.focused,
        )
        assert session.session_id == "session-123"
        assert session.mode == PracticeMode.focused
        assert session.questions == []


class TestProgressSummary:
    """Test ProgressSummary model."""

    def test_create_summary(self):
        summary = ProgressSummary(
            total_sessions=5,
            total_questions_practiced=25,
            avg_score=7.5,
            category_scores={"behavioral": 8.0, "technical": 7.0},
            weak_areas=["specificity", "structure"],
            improvement_trend="improving",
        )
        assert summary.total_sessions == 5
        assert summary.improvement_trend == "improving"


class TestPostInterviewLog:
    """Test PostInterviewLog model."""

    def test_create_log(self):
        from datetime import date

        log = PostInterviewLog(
            interview_date=date.today(),
            company="Acme Corp",
            position="Senior Engineer",
            questions_asked=["Tell me about yourself"],
            what_went_well=["System design"],
            what_stumped=["Behavioral questions"],
            outcome=InterviewOutcome.pending,
        )
        assert log.company == "Acme Corp"
        assert log.outcome == InterviewOutcome.pending
