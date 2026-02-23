"""Conversation thread management."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """A single message in a conversation."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)


class ConversationThread(BaseModel):
    """A conversation thread with message history."""
    user_id: str
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[dict] = None
    ) -> Message:
        """Add a message to the thread."""
        msg = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(msg)
        self.updated_at = datetime.now()
        return msg

    def get_recent_messages(self, count: int = 20) -> list[Message]:
        """Get the most recent N messages."""
        return self.messages[-count:] if self.messages else []
