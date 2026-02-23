"""Tests for evolution integration in session."""

import pytest
from unittest.mock import Mock, patch
from interview_prep_coach.conversation.session import ConversationSession
from interview_prep_coach.conversation.storage import MemoryStorage
from interview_prep_coach.evolution.state import EvolutionState


class TestSessionEvolution:
    """Tests for evolution integration."""

    @pytest.fixture
    def storage(self, tmp_path):
        return MemoryStorage(str(tmp_path))

    def test_session_has_evolution_state(self, storage):
        """Session should initialize with evolution state."""
        session = ConversationSession(user_id="test", storage=storage)
        assert hasattr(session, "evolution_state")
        assert isinstance(session.evolution_state, EvolutionState)

    def test_send_message_records_exchange(self, storage, monkeypatch):
        """send_message should record exchange in evolution state."""
        session = ConversationSession(user_id="test", storage=storage)

        # Mock the AI call
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        monkeypatch.setattr(
            session.client.messages,
            "create",
            Mock(return_value=mock_response)
        )
        # Mock pattern extractor
        monkeypatch.setattr(
            session.pattern_extractor,
            "extract",
            Mock(return_value=Mock(weaknesses=[], strengths=[], engagement_level="medium"))
        )

        initial_count = session.evolution_state.relationship.total_exchanges
        session.send_message("Hello")
        assert session.evolution_state.relationship.total_exchanges == initial_count + 1

    def test_send_message_extracts_patterns(self, storage, monkeypatch):
        """send_message should extract patterns from conversation."""
        session = ConversationSession(user_id="test", storage=storage)

        # Mock the AI call
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        monkeypatch.setattr(
            session.client.messages,
            "create",
            Mock(return_value=mock_response)
        )

        # Mock pattern extractor to track calls
        extract_called = []
        def mock_extract(user_msg, assistant_msg):
            extract_called.append((user_msg, assistant_msg))
            return Mock(weaknesses=["test weakness"], strengths=[], engagement_level="high")

        monkeypatch.setattr(session.pattern_extractor, "extract", mock_extract)

        session.send_message("I struggle with system design")

        assert len(extract_called) == 1
        assert "struggle" in extract_called[0][0].lower()

    def test_evolution_state_persists(self, storage, monkeypatch):
        """Evolution state should persist across sessions."""
        # First session
        session1 = ConversationSession(user_id="test", storage=storage)
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        monkeypatch.setattr(
            session1.client.messages,
            "create",
            Mock(return_value=mock_response)
        )
        monkeypatch.setattr(
            session1.pattern_extractor,
            "extract",
            Mock(return_value=Mock(weaknesses=[], strengths=[], engagement_level="medium"))
        )

        session1.send_message("Hello")
        session1.send_message("Hello again")

        # New session should have persisted state
        session2 = ConversationSession(user_id="test", storage=storage)
        assert session2.evolution_state.relationship.total_exchanges == 2
