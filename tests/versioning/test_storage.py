"""Tests for answer version storage."""

import pytest
from pathlib import Path
from datetime import datetime
from interview_prep_coach.versioning.storage import AnswerStorage
from interview_prep_coach.versioning.models import AnswerVersion, AnswerHistory


class TestAnswerStorage:
    """Tests for answer storage."""

    @pytest.fixture
    def storage(self, tmp_path):
        return AnswerStorage(data_dir=tmp_path)

    def test_save_and_load_history(self, storage):
        """Should persist and retrieve answer history."""
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

        storage.save(history)
        loaded = storage.load("q1")

        assert loaded is not None
        assert loaded.question_id == "q1"
        assert len(loaded.versions) == 1
        assert loaded.versions[0].content == "Test answer"

    def test_load_nonexistent_returns_none(self, storage):
        """Should return None for nonexistent history."""
        result = storage.load("nonexistent")
        assert result is None

    def test_list_question_ids(self, storage):
        """Should list all stored question IDs."""
        history1 = AnswerHistory(question_id="q1", question_text="Q1")
        history2 = AnswerHistory(question_id="q2", question_text="Q2")

        storage.save(history1)
        storage.save(history2)

        ids = storage.list_question_ids()
        assert "q1" in ids
        assert "q2" in ids
