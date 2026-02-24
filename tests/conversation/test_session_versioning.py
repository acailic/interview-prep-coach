"""Tests for answer versioning in session."""

import pytest
from interview_prep_coach.conversation.session import ConversationSession
from interview_prep_coach.conversation.storage import MemoryStorage


class TestSessionVersioning:
    """Tests for answer versioning integration."""

    @pytest.fixture
    def storage(self, tmp_path):
        return MemoryStorage(str(tmp_path))

    def test_detect_refinement_intent(self, storage):
        """Should detect when user wants to refine an answer."""
        session = ConversationSession(user_id="test", storage=storage)
        assert session._is_refinement_intent("let me try again")
        assert session._is_refinement_intent("another attempt")
        assert session._is_refinement_intent("let me refine that")
        assert not session._is_refinement_intent("new question")

    def test_detect_mark_best_intent(self, storage):
        """Should detect when user wants to mark best version."""
        session = ConversationSession(user_id="test", storage=storage)
        assert session._is_mark_best_intent("mark this as best")
        assert session._is_mark_best_intent("that's my best answer")
        assert not session._is_mark_best_intent("good answer")

    def test_detect_show_best_intent(self, storage):
        """Should detect when user wants to see best version."""
        session = ConversationSession(user_id="test", storage=storage)
        assert session._is_show_best_intent("show me my best")
        assert session._is_show_best_intent("what was my best answer")
        assert not session._is_show_best_intent("hello")

    def test_detect_compare_intent(self, storage):
        """Should detect when user wants to compare versions."""
        session = ConversationSession(user_id="test", storage=storage)
        assert session._is_compare_intent("compare versions")
        assert session._is_compare_intent("show the difference")
        assert not session._is_compare_intent("hello")
