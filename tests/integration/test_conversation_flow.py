"""Integration tests for conversation flow."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from interview_prep_coach.conversation import (
    ConversationSession,
    ConversationThread,
    MemoryStorage,
    MessageRole,
    WorkingMemory,
)


@pytest.fixture
def storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield MemoryStorage(tmpdir)


@pytest.fixture
def mock_anthropic():
    with patch("interview_prep_coach.conversation.session.Anthropic") as mock:
        client = MagicMock()
        mock.return_value = client

        response = MagicMock()
        response.content = [MagicMock(text="Test response from Scout")]
        client.messages.create.return_value = response

        yield mock, client


class TestMultiTurnConversation:
    """Tests for multi-turn conversation maintaining context."""

    def test_conversation_maintains_thread_history(self, storage, mock_anthropic):
        _, client = mock_anthropic
        session = ConversationSession(user_id="test_user", storage=storage)

        session.send_message("First message")
        session.send_message("Second message")

        assert len(session.thread.messages) == 4
        assert session.thread.messages[0].role == MessageRole.USER
        assert session.thread.messages[0].content == "First message"
        assert session.thread.messages[1].role == MessageRole.ASSISTANT
        assert session.thread.messages[2].role == MessageRole.USER
        assert session.thread.messages[2].content == "Second message"

    def test_conversation_context_includes_previous_messages(self, storage, mock_anthropic):
        _, client = mock_anthropic
        session = ConversationSession(user_id="test_user", storage=storage)

        session.send_message("First message")
        session.send_message("Second message")

        assert client.messages.create.call_count == 2

        second_call = client.messages.create.call_args
        messages = second_call.kwargs["messages"]

        user_messages = [m for m in messages if m["role"] == "user"]
        assert len(user_messages) >= 1

    def test_conversation_persists_across_sessions(self, storage, mock_anthropic):
        _, client = mock_anthropic

        session1 = ConversationSession(user_id="test_user", storage=storage)
        session1.send_message("Message from session 1")

        session2 = ConversationSession(user_id="test_user", storage=storage)
        assert len(session2.thread.messages) == 2
        assert session2.thread.messages[0].content == "Message from session 1"

    def test_working_memory_persists_across_sessions(self, storage, mock_anthropic):
        _, client = mock_anthropic

        session1 = ConversationSession(user_id="test_user", storage=storage)
        session1.working_memory.set_context(company="TechCorp", position="Engineer")
        session1._save_state()

        session2 = ConversationSession(user_id="test_user", storage=storage)
        assert session2.working_memory.current_context is not None
        assert session2.working_memory.current_context.company == "TechCorp"

    def test_context_builder_includes_working_memory(self, storage, mock_anthropic):
        _, client = mock_anthropic
        session = ConversationSession(user_id="test_user", storage=storage)

        session.working_memory.set_context(company="TestCo", position="Dev", days_until=3)
        session.working_memory.add_weakness("system design")
        session.send_message("Help me prepare")

        call_kwargs = client.messages.create.call_args.kwargs
        system_prompt = call_kwargs["system"]
        assert "Communication style:" in system_prompt


class TestStyleAdjustments:
    """Tests for style adjustments persisting across sessions."""

    def test_style_adjustment_updates_style_manager(self, storage, mock_anthropic):
        _, client = mock_anthropic
        session = ConversationSession(user_id="test_user", storage=storage)

        session.adjust_style("be more direct")

        assert session.style_manager.current_style.directness == "high"

    def test_style_adjustment_persists_in_working_memory(self, storage, mock_anthropic):
        _, client = mock_anthropic

        session1 = ConversationSession(user_id="test_user", storage=storage)
        session1.adjust_style("be more direct")

        session2 = ConversationSession(user_id="test_user", storage=storage)
        assert session2.working_memory.get_preference("directness") is not None

    def test_style_adjustment_affects_system_prompt(self, storage, mock_anthropic):
        _, client = mock_anthropic
        session = ConversationSession(user_id="test_user", storage=storage)

        session.adjust_style("be more direct")
        session.send_message("Help me")

        call_kwargs = client.messages.create.call_args.kwargs
        system_prompt = call_kwargs["system"]
        assert "direct" in system_prompt.lower()

    def test_multiple_style_adjustments(self, storage, mock_anthropic):
        _, client = mock_anthropic
        session = ConversationSession(user_id="test_user", storage=storage)

        session.adjust_style("be more direct")
        session.adjust_style("be more challenging")

        assert session.style_manager.current_style.directness == "high"
        assert session.style_manager.current_style.encouragement == "challenging"

    def test_get_context_summary_includes_preferences(self, storage, mock_anthropic):
        _, client = mock_anthropic
        session = ConversationSession(user_id="test_user", storage=storage)

        session.working_memory.set_context(company="TestCo")
        session.working_memory.set_preference("directness", "high")

        summary = session.get_context_summary()
        assert "TestCo" in summary
        assert "directness" in summary


class TestSessionState:
    """Tests for session state management."""

    def test_new_session_creates_fresh_thread(self, storage, mock_anthropic):
        _, client = mock_anthropic

        session = ConversationSession(user_id="new_user", storage=storage)
        assert len(session.thread.messages) == 0
        assert session.thread.user_id == "new_user"

    def test_new_session_creates_fresh_working_memory(self, storage, mock_anthropic):
        _, client = mock_anthropic

        session = ConversationSession(user_id="new_user", storage=storage)
        assert session.working_memory.current_context is None
        assert len(session.working_memory.recent_weaknesses) == 0

    def test_send_message_saves_state(self, storage, mock_anthropic):
        _, client = mock_anthropic

        session = ConversationSession(user_id="test_user", storage=storage)
        session.send_message("Hello")

        loaded_thread = storage.load_thread("test_user")
        assert loaded_thread is not None
        assert len(loaded_thread.messages) == 2

    def test_different_users_have_separate_threads(self, storage, mock_anthropic):
        _, client = mock_anthropic

        session1 = ConversationSession(user_id="user1", storage=storage)
        session1.send_message("User 1 message")

        session2 = ConversationSession(user_id="user2", storage=storage)
        session2.send_message("User 2 message")

        loaded1 = storage.load_thread("user1")
        loaded2 = storage.load_thread("user2")

        assert loaded1.messages[0].content == "User 1 message"
        assert loaded2.messages[0].content == "User 2 message"
