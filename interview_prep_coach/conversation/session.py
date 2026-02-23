"""Conversation session manager for Scout interview coach."""

from typing import Optional

from anthropic import Anthropic

from .context_builder import ContextBuilder
from .memory import WorkingMemory
from .storage import MemoryStorage
from .thread import ConversationThread, MessageRole
from ..coaching.style_manager import StyleManager


SCOUT_SYSTEM_PROMPT = """You are Scout, an interview prep coach. You're warm, supportive, and practical.

Your coaching philosophy:
- Preparation beats natural talent
- Every rejection is data, not defeat
- Progress over perfection
- Authenticity over acting"""


class ConversationSession:
    """Manages a conversation session with Scout."""

    def __init__(
        self,
        user_id: str,
        storage: MemoryStorage,
        api_key: Optional[str] = None,
    ):
        self.user_id = user_id
        self.storage = storage
        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()

        self.thread = storage.load_thread(user_id) or ConversationThread(user_id=user_id)
        self.working_memory = storage.load_working_memory(user_id) or WorkingMemory()
        self.style_manager = StyleManager()

    def send_message(self, content: str) -> str:
        self.thread.add_message(MessageRole.USER, content)

        context = (
            ContextBuilder()
            .with_working_memory(self.working_memory)
            .with_recent_messages(self.thread, count=10)
            .build()
        )

        style_modifier = self.style_manager.get_system_prompt_modifier()
        system_prompt = f"{SCOUT_SYSTEM_PROMPT}\n\nCommunication style: {style_modifier}"

        messages = []
        if context:
            messages.append({"role": "user", "content": f"[Context]\n{context}"})
            messages.append({"role": "assistant", "content": "I understand the context. How can I help you prepare?"})

        for msg in self.thread.get_recent_messages(10):
            if msg.role in (MessageRole.USER, MessageRole.ASSISTANT):
                messages.append({"role": msg.role.value, "content": msg.content})

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )

        assistant_content = response.content[0].text
        self.thread.add_message(MessageRole.ASSISTANT, assistant_content)

        self._save_state()

        return assistant_content

    def adjust_style(self, feedback: str) -> None:
        self.style_manager.learn_from_feedback(feedback, explicit=True)

        dimension = None
        feedback_lower = feedback.lower()
        if "direct" in feedback_lower or "gentle" in feedback_lower:
            dimension = "directness"
        elif "encourag" in feedback_lower or "challeng" in feedback_lower:
            dimension = "encouragement"
        elif "socratic" in feedback_lower or "instructional" in feedback_lower:
            dimension = "approach"
        elif "brief" in feedback_lower or "detailed" in feedback_lower:
            dimension = "depth"

        if dimension:
            self.working_memory.set_preference(dimension, feedback_lower)

        self._save_state()

    def get_context_summary(self) -> str:
        return self.working_memory.to_context_string()

    def _save_state(self) -> None:
        self.storage.save_thread(self.thread)
        self.storage.save_working_memory(self.user_id, self.working_memory)
