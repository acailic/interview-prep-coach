"""Tests for context builder."""

import pytest
from interview_prep_coach.conversation.context_builder import ContextBuilder
from interview_prep_coach.conversation.memory import WorkingMemory
from interview_prep_coach.conversation.thread import ConversationThread, MessageRole


class TestContextBuilder:
    def test_empty_builder(self):
        builder = ContextBuilder()
        result = builder.build()
        assert result == ""

    def test_with_working_memory(self):
        memory = WorkingMemory()
        memory.set_context(company="Acme", position="Engineer", days_until=3)
        memory.add_weakness("specificity")

        builder = ContextBuilder()
        result = builder.with_working_memory(memory).build()

        assert "CURRENT CONTEXT:" in result
        assert "Acme" in result
        assert "specificity" in result

    def test_with_recent_messages(self):
        thread = ConversationThread(user_id="user123")
        thread.add_message(MessageRole.USER, "Hello")
        thread.add_message(MessageRole.ASSISTANT, "Hi there!")

        builder = ContextBuilder()
        result = builder.with_recent_messages(thread).build()

        assert "RECENT CONVERSATION:" in result
        assert "USER: Hello" in result
        assert "ASSISTANT: Hi there!" in result

    def test_with_recent_messages_limited_count(self):
        thread = ConversationThread(user_id="user123")
        for i in range(10):
            thread.add_message(MessageRole.USER, f"Message {i}")

        builder = ContextBuilder()
        result = builder.with_recent_messages(thread, count=3).build()

        assert "Message 7" in result
        assert "Message 8" in result
        assert "Message 9" in result
        assert "Message 0" not in result

    def test_with_long_term_memories(self):
        builder = ContextBuilder()
        result = builder.with_long_term([
            "User prefers STAR method",
            "Strong at technical questions"
        ]).build()

        assert "RELEVANT HISTORY:" in result
        assert "- User prefers STAR method" in result
        assert "- Strong at technical questions" in result

    def test_with_empty_long_term_memories(self):
        builder = ContextBuilder()
        result = builder.with_long_term([]).build()
        assert result == ""

    def test_combined_context(self):
        memory = WorkingMemory()
        memory.set_context(company="TechCorp", days_until=5)

        thread = ConversationThread(user_id="user123")
        thread.add_message(MessageRole.USER, "Let's practice")
        thread.add_message(MessageRole.ASSISTANT, "Sure!")

        builder = ContextBuilder()
        result = (
            builder
            .with_working_memory(memory)
            .with_recent_messages(thread)
            .with_long_term(["Previous session went well"])
            .build()
        )

        assert "CURRENT CONTEXT:" in result
        assert "TechCorp" in result
        assert "RECENT CONVERSATION:" in result
        assert "Let's practice" in result
        assert "RELEVANT HISTORY:" in result
        assert "Previous session went well" in result

    def test_fluent_interface(self):
        builder = ContextBuilder()
        result = (
            builder
            .with_working_memory(WorkingMemory())
            .with_recent_messages(ConversationThread(user_id="u1"))
            .with_long_term([])
        )
        assert result is builder

    def test_empty_working_memory(self):
        memory = WorkingMemory()
        builder = ContextBuilder()
        result = builder.with_working_memory(memory).build()
        assert result == ""
