"""Tests for answer versioning models."""

from datetime import datetime
from interview_prep_coach.versioning.models import AnswerVersion, AnswerHistory


class TestAnswerVersion:
    """Tests for AnswerVersion model."""

    def test_create_version(self):
        """Should create an answer version with required fields."""
        version = AnswerVersion(
            version_number=1,
            content="I led a project that improved performance by 40%",
            created_at=datetime.now(),
            feedback="Good use of metrics",
            scores={"clarity": 7.5, "completeness": 6.0},
        )
        assert version.version_number == 1
        assert "40%" in version.content
        assert version.scores["clarity"] == 7.5

    def test_default_scores(self):
        """Should allow empty scores dict."""
        version = AnswerVersion(
            version_number=1,
            content="Test answer",
            created_at=datetime.now(),
            feedback="Test feedback",
        )
        assert version.scores == {}


class TestAnswerHistory:
    """Tests for AnswerHistory model."""

    def test_create_empty_history(self):
        """Should create history with no versions."""
        history = AnswerHistory(
            question_id="q1",
            question_text="Tell me about yourself",
        )
        assert history.question_id == "q1"
        assert history.versions == []
        assert history.best_version_id is None
        assert history.current_version_id == 0

    def test_add_version(self):
        """Should add a version to history."""
        history = AnswerHistory(
            question_id="q1",
            question_text="Tell me about yourself",
        )
        version = AnswerVersion(
            version_number=1,
            content="Test answer",
            created_at=datetime.now(),
            feedback="Good start",
        )
        history.add_version(version)
        assert len(history.versions) == 1
        assert history.current_version_id == 1

    def test_mark_best(self):
        """Should mark a version as best."""
        history = AnswerHistory(
            question_id="q1",
            question_text="Tell me about yourself",
        )
        version = AnswerVersion(
            version_number=1,
            content="Test answer",
            created_at=datetime.now(),
            feedback="Good start",
        )
        history.add_version(version)
        history.mark_best(1)
        assert history.best_version_id == 1

    def test_get_version(self):
        """Should retrieve a specific version."""
        history = AnswerHistory(
            question_id="q1",
            question_text="Tell me about yourself",
        )
        v1 = AnswerVersion(
            version_number=1,
            content="First attempt",
            created_at=datetime.now(),
            feedback="Okay",
        )
        v2 = AnswerVersion(
            version_number=2,
            content="Second attempt",
            created_at=datetime.now(),
            feedback="Better",
        )
        history.add_version(v1)
        history.add_version(v2)

        retrieved = history.get_version(2)
        assert retrieved.content == "Second attempt"
