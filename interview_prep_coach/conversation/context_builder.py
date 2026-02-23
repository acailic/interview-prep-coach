"""Context builder for assembling context from memory layers."""

from typing import Optional
from pydantic import BaseModel

from .memory import WorkingMemory
from .thread import ConversationThread


class ContextBuilder(BaseModel):
    """Assembles context from memory layers for AI calls."""

    working_memory_summary: Optional[str] = None
    recent_conversation: Optional[str] = None
    long_term_memories: Optional[str] = None

    def with_working_memory(self, memory: WorkingMemory) -> "ContextBuilder":
        self.working_memory_summary = memory.to_context_string() if memory.to_context_string() else None
        return self

    def with_recent_messages(self, thread: ConversationThread, count: int = 20) -> "ContextBuilder":
        messages = thread.get_recent_messages(count)
        if not messages:
            self.recent_conversation = None
            return self

        lines = []
        for msg in messages:
            role = msg.role.value.upper()
            lines.append(f"{role}: {msg.content}")

        self.recent_conversation = "\n".join(lines)
        return self

    def with_long_term(self, memories: list[str]) -> "ContextBuilder":
        if not memories:
            self.long_term_memories = None
            return self

        self.long_term_memories = "\n".join(f"- {m}" for m in memories)
        return self

    def build(self) -> str:
        sections = []

        if self.working_memory_summary:
            sections.append(f"CURRENT CONTEXT:\n{self.working_memory_summary}")

        if self.recent_conversation:
            sections.append(f"RECENT CONVERSATION:\n{self.recent_conversation}")

        if self.long_term_memories:
            sections.append(f"RELEVANT HISTORY:\n{self.long_term_memories}")

        if not sections:
            return ""

        return "\n\n".join(sections)
