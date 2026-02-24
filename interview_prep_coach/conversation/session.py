"""Conversation session manager for Scout interview coach."""

from typing import Optional

from anthropic import Anthropic

from .context_builder import ContextBuilder
from .memory import WorkingMemory
from .storage import MemoryStorage
from .thread import ConversationThread, MessageRole
from ..coaching.style_manager import StyleManager
from ..evolution.pattern_extractor import PatternExtractor
from ..evolution.state import EvolutionState
from ..job.context import JobContext
from ..versioning.storage import AnswerStorage
from interview_prep_coach.utils.logger import get_logger

logger = get_logger(__name__)


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
        self.evolution_state = storage.load_evolution_state(user_id) or EvolutionState()
        self.pattern_extractor = PatternExtractor(api_key=api_key)
        self.answer_storage = AnswerStorage(data_dir=storage.data_dir)
        self._current_question_id: str | None = None

    def send_message(self, content: str) -> str:
        # Store user message for extraction
        user_message = content
        self.thread.add_message(MessageRole.USER, content)

        context = (
            ContextBuilder()
            .with_working_memory(self.working_memory)
            .with_recent_messages(self.thread, count=10)
            .build()
        )

        style_modifier = self.style_manager.get_system_prompt_modifier()
        phase_modifier = self.evolution_state.relationship.get_phase_modifier()
        system_prompt = f"{SCOUT_SYSTEM_PROMPT}\n\nCommunication style: {style_modifier}\nRelationship: {phase_modifier}"

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

        # Evolution: Extract patterns
        patterns = self.pattern_extractor.extract(user_message, assistant_content)
        for weakness in patterns.weaknesses:
            self.working_memory.add_weakness(weakness)
        for strength in patterns.strengths:
            self.working_memory.add_strength(strength)

        # Evolution: Record exchange and engagement
        self.evolution_state.record_exchange()
        style_key = f"{self.style_manager.current_style.approach}:{self.style_manager.current_style.encouragement}"
        self.evolution_state.record_style_outcome(style_key, patterns.engagement_level)

        # Evolution: Apply style drift every 10 exchanges
        if self.evolution_state.relationship.total_exchanges % 10 == 0:
            self._apply_style_drift()

        self._save_state()

        return assistant_content

    def _apply_style_drift(self) -> None:
        """Apply style drift based on effectiveness tracking."""
        recommended = self.evolution_state.effectiveness.get_recommended_style()
        if recommended:
            # Parse and nudge style toward recommended
            parts = recommended.split(":")
            if len(parts) >= 2:
                approach, encouragement = parts[0], parts[1]
                from ..coaching.style_manager import StyleDimension
                if self.style_manager.current_style.approach != approach:
                    self.style_manager.adjust(StyleDimension.APPROACH, approach)
                if self.style_manager.current_style.encouragement != encouragement:
                    self.style_manager.adjust(StyleDimension.ENCOURAGEMENT, encouragement)

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

    def set_job_context(self, job: JobContext) -> None:
        """Set job context for personalized coaching."""
        self.working_memory.set_job_context(job)
        self._save_state()

    def _save_state(self) -> None:
        self.storage.save_thread(self.thread)
        self.storage.save_working_memory(self.user_id, self.working_memory)
        self.storage.save_evolution_state(self.user_id, self.evolution_state)

    def _is_refinement_intent(self, message: str) -> bool:
        """Detect if user wants to refine their last answer."""
        triggers = [
            "let me try again",
            "another attempt",
            "let me refine",
            "one more time",
            "try that again",
            "let me redo",
        ]
        return any(t in message.lower() for t in triggers)

    def _is_mark_best_intent(self, message: str) -> bool:
        """Detect if user wants to mark current version as best."""
        triggers = [
            "mark this as best",
            "that's my best",
            "this is the best version",
            "mark as best",
        ]
        return any(t in message.lower() for t in triggers)

    def _is_show_best_intent(self, message: str) -> bool:
        """Detect if user wants to see their best version."""
        triggers = [
            "show me my best",
            "what was my best answer",
            "show best version",
        ]
        return any(t in message.lower() for t in triggers)

    def _is_compare_intent(self, message: str) -> bool:
        """Detect if user wants to compare versions."""
        triggers = [
            "compare versions",
            "show the difference",
            "how did i improve",
            "compare my answers",
        ]
        return any(t in message.lower() for t in triggers)
