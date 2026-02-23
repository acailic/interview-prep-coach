"""Conversation management module."""

from .memory import InterviewContext, WorkingMemory
from .thread import ConversationThread, Message, MessageRole

__all__ = [
    "ConversationThread",
    "InterviewContext",
    "Message",
    "MessageRole",
    "WorkingMemory",
]
