"""Tests for conversation thread management."""

import pytest
from datetime import datetime
from interview_prep_coach.conversation.thread import (
    ConversationThread,
    Message,
    MessageRole,
)


class TestMessage:
    def test_create_user_message(self):
        msg = Message(role=MessageRole.USER, content="Hello Scout")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello Scout"
        assert isinstance(msg.timestamp, datetime)

    def test_create_assistant_message(self):
        msg = Message(role=MessageRole.ASSISTANT, content="Hey! Ready to practice?")
        assert msg.role == MessageRole.ASSISTANT
        assert "Ready" in msg.content


class TestConversationThread:
    def test_create_empty_thread(self):
        thread = ConversationThread(user_id="user123")
        assert thread.user_id == "user123"
        assert len(thread.messages) == 0

    def test_add_message(self):
        thread = ConversationThread(user_id="user123")
        thread.add_message(MessageRole.USER, "Let's practice")
        assert len(thread.messages) == 1
        assert thread.messages[0].content == "Let's practice"

    def test_get_recent_messages(self):
        thread = ConversationThread(user_id="user123")
        for i in range(25):
            thread.add_message(MessageRole.USER, f"Message {i}")

        recent = thread.get_recent_messages(count=20)
        assert len(recent) == 20
        assert recent[-1].content == "Message 24"
