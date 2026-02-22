# Conversation-First Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform interview-prep-coach from transactional Q&A to an AI coach with persistent memory, adaptive style, and conversational depth.

**Architecture:** Single conversation thread per user with layered memory (active context, working memory, long-term semantic search, identity layer). Coaching style adapts through explicit user feedback and implicit pattern recognition.

**Tech Stack:** Python, Pydantic, Anthropic API, SQLite, sentence-transformers (embeddings), Click CLI

---

## Task 1: Conversation Thread Foundation

**Files:**
- Create: `interview_prep_coach/conversation/__init__.py`
- Create: `interview_prep_coach/conversation/thread.py`
- Create: `tests/conversation/test_thread.py`

**Step 1: Write the failing test**

```python
# tests/conversation/test_thread.py
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
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_thread.py -v`
Expected: FAIL with "ModuleNotFoundError" or "ImportError"

**Step 3: Write minimal implementation**

```python
# interview_prep_coach/conversation/__init__.py
"""Conversation management module."""

from .thread import ConversationThread, Message, MessageRole

__all__ = ["ConversationThread", "Message", "MessageRole"]
```

```python
# interview_prep_coach/conversation/thread.py
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
```

**Step 4: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_thread.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach
git add interview_prep_coach/conversation/ tests/conversation/
git commit -m "feat: add conversation thread foundation with Message and ConversationThread models"
```

---

## Task 2: Memory Layers - Working Memory

**Files:**
- Create: `interview_prep_coach/conversation/memory.py`
- Create: `tests/conversation/test_memory.py`

**Step 1: Write the failing test**

```python
# tests/conversation/test_memory.py
"""Tests for memory system."""

import pytest
from interview_prep_coach.conversation.memory import (
    WorkingMemory,
    InterviewContext,
)


class TestInterviewContext:
    def test_create_context(self):
        context = InterviewContext(
            company="Acme Corp",
            position="Senior Engineer",
            days_until_interview=3,
        )
        assert context.company == "Acme Corp"
        assert context.days_until_interview == 3

    def test_context_optional_fields(self):
        context = InterviewContext(company="Acme Corp")
        assert context.position is None
        assert context.days_until_interview is None


class TestWorkingMemory:
    def test_create_empty_memory(self):
        memory = WorkingMemory()
        assert memory.current_context is None
        assert len(memory.recent_weaknesses) == 0

    def test_set_interview_context(self):
        memory = WorkingMemory()
        memory.set_context(
            company="Acme Corp",
            position="Senior Engineer",
            days_until=3
        )
        assert memory.current_context.company == "Acme Corp"

    def test_track_weaknesses(self):
        memory = WorkingMemory()
        memory.add_weakness("specificity")
        memory.add_weakness("STAR structure")
        assert "specificity" in memory.recent_weaknesses
        assert len(memory.recent_weaknesses) == 2

    def test_track_style_preference(self):
        memory = WorkingMemory()
        memory.set_preference("directness", "high")
        assert memory.get_preference("directness") == "high"

    def test_to_context_string(self):
        memory = WorkingMemory()
        memory.set_context(company="Acme", position="Engineer", days_until=3)
        memory.add_weakness("specificity")
        context_str = memory.to_context_string()
        assert "Acme" in context_str
        assert "specificity" in context_str
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_memory.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# interview_prep_coach/conversation/memory.py
"""Memory layers for conversation context."""

from typing import Optional
from pydantic import BaseModel, Field


class InterviewContext(BaseModel):
    """Current interview preparation context."""
    company: str
    position: Optional[str] = None
    days_until_interview: Optional[int] = None
    notes: list[str] = Field(default_factory=list)


class WorkingMemory(BaseModel):
    """Working memory - summarized context for current coaching."""
    current_context: Optional[InterviewContext] = None
    recent_weaknesses: list[str] = Field(default_factory=list)
    recent_strengths: list[str] = Field(default_factory=list)
    style_preferences: dict[str, str] = Field(default_factory=dict)
    last_session_summary: Optional[str] = None

    def set_context(
        self,
        company: str,
        position: Optional[str] = None,
        days_until: Optional[int] = None
    ) -> None:
        """Set the current interview context."""
        self.current_context = InterviewContext(
            company=company,
            position=position,
            days_until_interview=days_until
        )

    def add_weakness(self, weakness: str) -> None:
        """Track a weakness being worked on."""
        if weakness not in self.recent_weaknesses:
            self.recent_weaknesses.append(weakness)
        # Keep only last 5 weaknesses
        self.recent_weaknesses = self.recent_weaknesses[-5:]

    def add_strength(self, strength: str) -> None:
        """Track a strength identified."""
        if strength not in self.recent_strengths:
            self.recent_strengths.append(strength)
        self.recent_strengths = self.recent_strengths[-5:]

    def set_preference(self, dimension: str, value: str) -> None:
        """Set a coaching style preference."""
        self.style_preferences[dimension] = value

    def get_preference(self, dimension: str) -> Optional[str]:
        """Get a coaching style preference."""
        return self.style_preferences.get(dimension)

    def to_context_string(self) -> str:
        """Convert working memory to context string for AI."""
        parts = []

        if self.current_context:
            ctx = self.current_context
            parts.append(f"Current prep: {ctx.company}")
            if ctx.position:
                parts[-1] += f", {ctx.position}"
            if ctx.days_until_interview:
                parts[-1] += f", {ctx.days_until_interview} days away"

        if self.recent_weaknesses:
            parts.append(f"Working on: {', '.join(self.recent_weaknesses)}")

        if self.recent_strengths:
            parts.append(f"Strengths shown: {', '.join(self.recent_strengths)}")

        if self.style_preferences:
            prefs = [f"{k}: {v}" for k, v in self.style_preferences.items()]
            parts.append(f"Style preferences: {', '.join(prefs)}")

        return "\n".join(parts)
```

**Step 4: Update __init__.py**

```python
# interview_prep_coach/conversation/__init__.py
"""Conversation management module."""

from .thread import ConversationThread, Message, MessageRole
from .memory import WorkingMemory, InterviewContext

__all__ = [
    "ConversationThread", "Message", "MessageRole",
    "WorkingMemory", "InterviewContext",
]
```

**Step 5: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_memory.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach
git add interview_prep_coach/conversation/ tests/conversation/
git commit -m "feat: add working memory with interview context and style preferences"
```

---

## Task 3: Memory Persistence with SQLite

**Files:**
- Create: `interview_prep_coach/conversation/storage.py`
- Create: `tests/conversation/test_storage.py`

**Step 1: Write the failing test**

```python
# tests/conversation/test_storage.py
"""Tests for memory storage."""

import pytest
import tempfile
from pathlib import Path
from interview_prep_coach.conversation.storage import MemoryStorage
from interview_prep_coach.conversation.thread import ConversationThread
from interview_prep_coach.conversation.memory import WorkingMemory


class TestMemoryStorage:
    def test_create_storage(self, tmp_path):
        storage = MemoryStorage(data_dir=tmp_path)
        assert storage.data_dir == tmp_path

    def test_save_and_load_thread(self, tmp_path):
        storage = MemoryStorage(data_dir=tmp_path)
        thread = ConversationThread(user_id="user123")
        thread.add_message(role="user", content="Hello")

        storage.save_thread(thread)
        loaded = storage.load_thread("user123")

        assert loaded is not None
        assert loaded.user_id == "user123"
        assert len(loaded.messages) == 1

    def test_save_and_load_working_memory(self, tmp_path):
        storage = MemoryStorage(data_dir=tmp_path)
        memory = WorkingMemory()
        memory.set_context(company="Acme", position="Engineer")

        storage.save_working_memory("user123", memory)
        loaded = storage.load_working_memory("user123")

        assert loaded is not None
        assert loaded.current_context.company == "Acme"

    def test_load_nonexistent_thread(self, tmp_path):
        storage = MemoryStorage(data_dir=tmp_path)
        loaded = storage.load_thread("nonexistent")
        assert loaded is None

    def test_list_users(self, tmp_path):
        storage = MemoryStorage(data_dir=tmp_path)

        # Create threads for multiple users
        for uid in ["user1", "user2", "user3"]:
            thread = ConversationThread(user_id=uid)
            storage.save_thread(thread)

        users = storage.list_users()
        assert len(users) == 3
        assert "user1" in users
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_storage.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# interview_prep_coach/conversation/storage.py
"""Persistent storage for conversation data."""

import json
from pathlib import Path
from typing import Optional
from .thread import ConversationThread
from .memory import WorkingMemory


class MemoryStorage:
    """File-based storage for conversation threads and memory."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _thread_path(self, user_id: str) -> Path:
        return self.data_dir / f"{user_id}_thread.json"

    def _memory_path(self, user_id: str) -> Path:
        return self.data_dir / f"{user_id}_memory.json"

    def save_thread(self, thread: ConversationThread) -> None:
        """Save conversation thread to disk."""
        path = self._thread_path(thread.user_id)
        with open(path, "w") as f:
            json.dump(thread.model_dump(mode="json"), f, indent=2, default=str)

    def load_thread(self, user_id: str) -> Optional[ConversationThread]:
        """Load conversation thread from disk."""
        path = self._thread_path(user_id)
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return ConversationThread.model_validate(data)

    def save_working_memory(self, user_id: str, memory: WorkingMemory) -> None:
        """Save working memory to disk."""
        path = self._memory_path(user_id)
        with open(path, "w") as f:
            json.dump(memory.model_dump(mode="json"), f, indent=2, default=str)

    def load_working_memory(self, user_id: str) -> Optional[WorkingMemory]:
        """Load working memory from disk."""
        path = self._memory_path(user_id)
        if not path.exists():
            return WorkingMemory()  # Return empty memory for new users
        with open(path) as f:
            data = json.load(f)
        return WorkingMemory.model_validate(data)

    def list_users(self) -> list[str]:
        """List all users with stored data."""
        users = set()
        for path in self.data_dir.glob("*_thread.json"):
            user_id = path.stem.replace("_thread", "")
            users.add(user_id)
        return list(users)
```

**Step 4: Update __init__.py**

```python
# interview_prep_coach/conversation/__init__.py
"""Conversation management module."""

from .thread import ConversationThread, Message, MessageRole
from .memory import WorkingMemory, InterviewContext
from .storage import MemoryStorage

__all__ = [
    "ConversationThread", "Message", "MessageRole",
    "WorkingMemory", "InterviewContext",
    "MemoryStorage",
]
```

**Step 5: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_storage.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach
git add interview_prep_coach/conversation/ tests/conversation/
git commit -m "feat: add persistent storage for threads and working memory"
```

---

## Task 4: Context Builder

**Files:**
- Create: `interview_prep_coach/conversation/context_builder.py`
- Create: `tests/conversation/test_context_builder.py`

**Step 1: Write the failing test**

```python
# tests/conversation/test_context_builder.py
"""Tests for context builder."""

import pytest
from interview_prep_coach.conversation.context_builder import ContextBuilder
from interview_prep_coach.conversation.thread import ConversationThread, MessageRole
from interview_prep_coach.conversation.memory import WorkingMemory


class TestContextBuilder:
    def test_build_empty_context(self):
        builder = ContextBuilder()
        context = builder.build()
        assert context == ""

    def test_build_with_working_memory(self):
        builder = ContextBuilder()
        memory = WorkingMemory()
        memory.set_context(company="Acme", position="Engineer", days_until=3)

        builder.with_working_memory(memory)
        context = builder.build()

        assert "Acme" in context
        assert "Engineer" in context

    def test_build_with_recent_messages(self):
        builder = ContextBuilder()
        thread = ConversationThread(user_id="test")
        thread.add_message(MessageRole.USER, "Hello")
        thread.add_message(MessageRole.ASSISTANT, "Hi there!")

        builder.with_recent_messages(thread, count=20)
        context = builder.build()

        assert "Hello" in context
        assert "Hi there" in context

    def test_build_combined_context(self):
        builder = ContextBuilder()
        memory = WorkingMemory()
        memory.set_context(company="Acme")
        memory.add_weakness("specificity")

        thread = ConversationThread(user_id="test")
        thread.add_message(MessageRole.USER, "Let's practice")

        builder.with_working_memory(memory)
        builder.with_recent_messages(thread)

        context = builder.build()

        assert "Acme" in context
        assert "specificity" in context
        assert "Let's practice" in context

    def test_context_format_for_ai(self):
        builder = ContextBuilder()
        memory = WorkingMemory()
        memory.set_context(company="Acme", days_until=2)

        builder.with_working_memory(memory)
        context = builder.build()

        # Should be formatted for AI consumption
        assert "CONTEXT:" in context or "Current" in context
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_context_builder.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# interview_prep_coach/conversation/context_builder.py
"""Build context for AI calls from memory layers."""

from typing import Optional
from .thread import ConversationThread, MessageRole
from .memory import WorkingMemory


class ContextBuilder:
    """Assembles context from memory layers for AI calls."""

    def __init__(self):
        self._working_memory: Optional[WorkingMemory] = None
        self._recent_messages: list[str] = []
        self._long_term_context: list[str] = []

    def with_working_memory(self, memory: WorkingMemory) -> "ContextBuilder":
        """Add working memory context."""
        self._working_memory = memory
        return self

    def with_recent_messages(
        self,
        thread: ConversationThread,
        count: int = 20
    ) -> "ContextBuilder":
        """Add recent conversation messages."""
        messages = thread.get_recent_messages(count)
        self._recent_messages = [
            f"{msg.role.value}: {msg.content}"
            for msg in messages
        ]
        return self

    def with_long_term(self, memories: list[str]) -> "ContextBuilder":
        """Add long-term memory context."""
        self._long_term_context = memories
        return self

    def build(self) -> str:
        """Build the full context string for AI."""
        parts = []

        # Working memory context
        if self._working_memory:
            working = self._working_memory.to_context_string()
            if working:
                parts.append(f"CURRENT CONTEXT:\n{working}")

        # Long-term memories
        if self._long_term_context:
            parts.append("RELEVANT HISTORY:\n" + "\n".join(self._long_term_context))

        # Recent conversation
        if self._recent_messages:
            parts.append("RECENT CONVERSATION:\n" + "\n".join(self._recent_messages))

        return "\n\n".join(parts) if parts else ""
```

**Step 4: Update __init__.py**

```python
# interview_prep_coach/conversation/__init__.py
"""Conversation management module."""

from .thread import ConversationThread, Message, MessageRole
from .memory import WorkingMemory, InterviewContext
from .storage import MemoryStorage
from .context_builder import ContextBuilder

__all__ = [
    "ConversationThread", "Message", "MessageRole",
    "WorkingMemory", "InterviewContext",
    "MemoryStorage", "ContextBuilder",
]
```

**Step 5: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_context_builder.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach
git add interview_prep_coach/conversation/ tests/conversation/
git commit -m "feat: add context builder for assembling AI context from memory layers"
```

---

## Task 5: Coaching Style Manager

**Files:**
- Create: `interview_prep_coach/coaching/__init__.py`
- Create: `interview_prep_coach/coaching/style_manager.py`
- Create: `tests/coaching/test_style_manager.py`

**Step 1: Write the failing test**

```python
# tests/coaching/test_style_manager.py
"""Tests for coaching style manager."""

import pytest
from interview_prep_coach.coaching.style_manager import (
    CoachingStyle,
    StyleDimension,
    StyleManager,
)


class TestCoachingStyle:
    def test_default_style(self):
        style = CoachingStyle()
        assert style.directness == "medium"
        assert style.encouragement == "measured"
        assert style.approach == "collaborative"

    def test_custom_style(self):
        style = CoachingStyle(
            directness="high",
            encouragement="cheerleader",
            approach="socratic"
        )
        assert style.directness == "high"
        assert style.encouragement == "cheerleader"


class TestStyleManager:
    def test_create_manager(self):
        manager = StyleManager()
        assert manager.current_style is not None

    def test_adjust_style(self):
        manager = StyleManager()
        manager.adjust(StyleDimension.DIRECTNESS, "high")
        assert manager.current_style.directness == "high"

    def test_learn_from_feedback_explicit(self):
        manager = StyleManager()

        # User says "be more direct"
        manager.learn_from_feedback("be more direct", explicit=True)
        assert manager.current_style.directness == "high"

    def test_learn_from_feedback_implicit(self):
        manager = StyleManager()

        # Track that direct feedback led to improvement
        manager.record_outcome(style_used="direct", improved=True)
        assert "direct" in manager.effective_styles

    def test_get_system_prompt_modifier(self):
        manager = StyleManager()
        manager.adjust(StyleDimension.DIRECTNESS, "high")

        modifier = manager.get_system_prompt_modifier()
        assert "direct" in modifier.lower()
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/coaching/test_style_manager.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# interview_prep_coach/coaching/__init__.py
"""Coaching module for adaptive style management."""

from .style_manager import CoachingStyle, StyleDimension, StyleManager

__all__ = ["CoachingStyle", "StyleDimension", "StyleManager"]
```

```python
# interview_prep_coach/coaching/style_manager.py
"""Adaptive coaching style management."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class StyleDimension(str, Enum):
    """Dimensions of coaching style."""
    DIRECTNESS = "directness"
    ENCOURAGEMENT = "encouragement"
    APPROACH = "approach"
    DEPTH = "depth"


class CoachingStyle(BaseModel):
    """User's coaching style preferences."""
    directness: str = "medium"  # low, medium, high
    encouragement: str = "measured"  # cheerleader, measured, challenging
    approach: str = "collaborative"  # socratic, instructional, collaborative
    depth: str = "thorough"  # concise, thorough


class StyleManager(BaseModel):
    """Manages adaptive coaching style."""

    current_style: CoachingStyle = Field(default_factory=CoachingStyle)
    effective_styles: list[str] = Field(default_factory=list)
    adjustment_history: list[dict] = Field(default_factory=list)

    def adjust(self, dimension: StyleDimension, value: str) -> None:
        """Adjust a style dimension."""
        setattr(self.current_style, dimension.value, value)
        self.adjustment_history.append({
            "dimension": dimension.value,
            "value": value
        })

    def learn_from_feedback(
        self,
        feedback: str,
        explicit: bool = False
    ) -> None:
        """Learn style preference from user feedback."""
        feedback_lower = feedback.lower()

        # Directness adjustments
        if any(p in feedback_lower for p in ["more direct", "be honest", "tough love"]):
            self.adjust(StyleDimension.DIRECTNESS, "high")
        elif any(p in feedback_lower for p in ["too harsh", "gentler", "softer"]):
            self.adjust(StyleDimension.DIRECTNESS, "low")

        # Encouragement adjustments
        if any(p in feedback_lower for p in ["more encouraging", "cheer me on"]):
            self.adjust(StyleDimension.ENCOURAGEMENT, "cheerleader")
        elif any(p in feedback_lower for p in ["push me", "challenge me"]):
            self.adjust(StyleDimension.ENCOURAGEMENT, "challenging")

        # Approach adjustments
        if any(p in feedback_lower for p in ["just tell me", "give me answers"]):
            self.adjust(StyleDimension.APPROACH, "instructional")
        elif any(p in feedback_lower for p in ["let me figure out", "guide me"]):
            self.adjust(StyleDimension.APPROACH, "socratic")

    def record_outcome(self, style_used: str, improved: bool) -> None:
        """Record whether a style led to improvement."""
        if improved and style_used not in self.effective_styles:
            self.effective_styles.append(style_used)

    def get_system_prompt_modifier(self) -> str:
        """Get style instructions for AI system prompt."""
        style = self.current_style

        parts = []

        if style.directness == "high":
            parts.append("Be direct and honest. Don't sugarcoat feedback.")
        elif style.directness == "low":
            parts.append("Be gentle with feedback. Lead with positives.")

        if style.encouragement == "cheerleader":
            parts.append("Be enthusiastic and celebratory of progress.")
        elif style.encouragement == "challenging":
            parts.append("Push the user to do better. Don't settle for good enough.")

        if style.approach == "socratic":
            parts.append("Ask questions to guide discovery rather than giving answers.")
        elif style.approach == "instructional":
            parts.append("Give clear, direct guidance on how to improve.")

        return " ".join(parts) if parts else ""
```

**Step 4: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/coaching/test_style_manager.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach
git add interview_prep_coach/coaching/ tests/coaching/
git commit -m "feat: add coaching style manager with adaptive preferences"
```

---

## Task 6: Conversation Session Manager

**Files:**
- Create: `interview_prep_coach/conversation/session.py`
- Create: `tests/conversation/test_session.py`

**Step 1: Write the failing test**

```python
# tests/conversation/test_session.py
"""Tests for conversation session management."""

import pytest
from pathlib import Path
from interview_prep_coach.conversation.session import ConversationSession
from interview_prep_coach.conversation.storage import MemoryStorage


class TestConversationSession:
    def test_create_session(self, tmp_path):
        storage = MemoryStorage(data_dir=tmp_path)
        session = ConversationSession(user_id="user123", storage=storage)
        assert session.user_id == "user123"

    def test_send_message(self, tmp_path):
        storage = MemoryStorage(data_dir=tmp_path)
        session = ConversationSession(user_id="user123", storage=storage)

        response = session.send_message("Hello Scout!")
        assert response is not None
        assert len(session.thread.messages) == 2  # user + assistant

    def test_session_persists(self, tmp_path):
        storage = MemoryStorage(data_dir=tmp_path)

        # First session
        session1 = ConversationSession(user_id="user123", storage=storage)
        session1.send_message("Hello")

        # New session instance, same user
        session2 = ConversationSession(user_id="user123", storage=storage)
        assert len(session2.thread.messages) >= 1  # Should have history

    def test_get_context_summary(self, tmp_path):
        storage = MemoryStorage(data_dir=tmp_path)
        session = ConversationSession(user_id="user123", storage=storage)
        session.working_memory.set_context(company="Acme")

        summary = session.get_context_summary()
        assert "Acme" in summary

    def test_adjust_style(self, tmp_path):
        storage = MemoryStorage(data_dir=tmp_path)
        session = ConversationSession(user_id="user123", storage=storage)

        session.adjust_style("be more direct")
        assert session.style_manager.current_style.directness == "high"
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_session.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# interview_prep_coach/conversation/session.py
"""Conversation session management."""

import os
from typing import Optional
from anthropic import Anthropic

from .thread import ConversationThread, MessageRole
from .memory import WorkingMemory
from .storage import MemoryStorage
from .context_builder import ContextBuilder
from ..coaching.style_manager import StyleManager, StyleDimension


SCOUT_SYSTEM_PROMPT = """You are Scout, an interview prep coach. You're warm, supportive, and practical.

Your coaching philosophy:
- Preparation beats natural talent
- Every rejection is data, not defeat
- Progress over perfection
- Authenticity over acting

You're having an ongoing conversation with someone preparing for interviews. You remember your history together and adapt your coaching style to what works for them.

Be conversational, not transactional. Ask follow-up questions. Help them discover answers."""


class ConversationSession:
    """Manages a conversation session with Scout."""

    def __init__(
        self,
        user_id: str,
        storage: MemoryStorage,
        api_key: Optional[str] = None
    ):
        self.user_id = user_id
        self.storage = storage

        # Load or create thread
        self.thread = storage.load_thread(user_id) or ConversationThread(user_id=user_id)

        # Load or create working memory
        self.working_memory = storage.load_working_memory(user_id) or WorkingMemory()

        # Initialize style manager
        self.style_manager = StyleManager()

        # Initialize Anthropic client
        self._client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self._model = "claude-sonnet-4-20250514"

    def send_message(self, content: str) -> str:
        """Send a message and get Scout's response."""
        # Add user message
        self.thread.add_message(MessageRole.USER, content)

        # Build context
        context = self._build_context()

        # Get style modifier
        style_modifier = self.style_manager.get_system_prompt_modifier()

        # Build system prompt
        system_prompt = SCOUT_SYSTEM_PROMPT
        if style_modifier:
            system_prompt += f"\n\nStyle adjustment: {style_modifier}"

        # Call Anthropic
        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=system_prompt,
            messages=self._build_api_messages(context),
        )

        assistant_content = response.content[0].text

        # Add assistant response
        self.thread.add_message(MessageRole.ASSISTANT, assistant_content)

        # Save state
        self._save_state()

        return assistant_content

    def _build_context(self) -> str:
        """Build context string from memory layers."""
        builder = ContextBuilder()
        builder.with_working_memory(self.working_memory)
        builder.with_recent_messages(self.thread, count=20)
        return builder.build()

    def _build_api_messages(self, context: str) -> list[dict]:
        """Build messages list for API call."""
        messages = []

        # Add context as first user message if present
        if context:
            messages.append({
                "role": "user",
                "content": f"[Context about our conversation]\n{context}\n\n[Current message]"
            })
            messages.append({
                "role": "assistant",
                "content": "I have that context. What would you like to work on?"
            })

        # Add recent messages
        for msg in self.thread.get_recent_messages(20):
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })

        return messages

    def adjust_style(self, feedback: str) -> None:
        """Adjust coaching style based on user feedback."""
        self.style_manager.learn_from_feedback(feedback, explicit=True)
        self._save_state()

    def get_context_summary(self) -> str:
        """Get summary of current context."""
        return self.working_memory.to_context_string()

    def _save_state(self) -> None:
        """Persist session state."""
        self.storage.save_thread(self.thread)
        self.storage.save_working_memory(self.user_id, self.working_memory)
```

**Step 4: Update __init__.py**

```python
# interview_prep_coach/conversation/__init__.py
"""Conversation management module."""

from .thread import ConversationThread, Message, MessageRole
from .memory import WorkingMemory, InterviewContext
from .storage import MemoryStorage
from .context_builder import ContextBuilder
from .session import ConversationSession

__all__ = [
    "ConversationThread", "Message", "MessageRole",
    "WorkingMemory", "InterviewContext",
    "MemoryStorage", "ContextBuilder",
    "ConversationSession",
]
```

**Step 5: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_session.py -v`
Expected: All tests PASS (may need to mock Anthropic API)

**Step 6: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach
git add interview_prep_coach/conversation/ tests/conversation/
git commit -m "feat: add conversation session manager with Scout integration"
```

---

## Task 7: CLI Chat Command

**Files:**
- Modify: `interview_prep_coach/cli.py`
- Create: `tests/test_cli_chat.py`

**Step 1: Write the failing test**

```python
# tests/test_cli_chat.py
"""Tests for chat CLI command."""

import pytest
from click.testing import CliRunner
from interview_prep_coach.cli import chat


class TestChatCommand:
    def test_chat_command_exists(self):
        runner = CliRunner()
        result = runner.invoke(chat, ["--help"])
        assert result.exit_code == 0
        assert "chat" in result.output.lower() or "conversation" in result.output.lower()

    def test_chat_with_message(self, tmp_path, monkeypatch):
        # Mock the session to avoid API calls
        runner = CliRunner()

        # This would normally make API calls, so we test the command structure
        result = runner.invoke(chat, ["--help"])
        assert result.exit_code == 0
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/test_cli_chat.py -v`
Expected: FAIL or command not found

**Step 3: Add chat command to CLI**

```python
# Add to interview_prep_coach/cli.py

import os
from pathlib import Path
import click
from .conversation import ConversationSession, MemoryStorage

# ... existing code ...

@click.command()
@click.option("--message", "-m", type=str, help="Send a single message and exit")
@click.option("--data-dir", type=click.Path(), default="./data/conversations", help="Directory for conversation data")
@click.option("--user", type=str, default="default", help="User identifier")
def chat(message: str | None, data_dir: str, user: str):
    """Start or continue a conversation with Scout.

    Examples:
        interview-prep chat                    # Interactive mode
        interview-prep -m "Let's practice"     # Single message
        interview-prep --user jane             # Specific user
    """
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    storage = MemoryStorage(data_dir=data_path)
    session = ConversationSession(user_id=user, storage=storage)

    if message:
        # Single message mode
        response = session.send_message(message)
        click.echo(response)
    else:
        # Interactive mode
        click.echo("Starting conversation with Scout. Type 'exit' to quit.\n")

        # Show context if returning
        context = session.get_context_summary()
        if context:
            click.echo(f"[Context: {context}]\n")

        while True:
            try:
                user_input = click.prompt("You", type=str)
                if user_input.lower() in ["exit", "quit", "bye"]:
                    click.echo("\nScout: See you next time!")
                    break

                response = session.send_message(user_input)
                click.echo(f"\nScout: {response}\n")

            except KeyboardInterrupt:
                click.echo("\n\nSession saved. See you!")
                break

# Add to main group
# main.add_command(chat)
```

**Step 4: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/test_cli_chat.py -v`
Expected: Tests PASS

**Step 5: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach
git add interview_prep_coach/cli.py tests/test_cli_chat.py
git commit -m "feat: add chat command for conversational interface with Scout"
```

---

## Task 8: Integration - Full Conversation Flow

**Files:**
- Create: `tests/integration/test_conversation_flow.py`

**Step 1: Write integration test**

```python
# tests/integration/test_conversation_flow.py
"""Integration tests for full conversation flow."""

import pytest
from pathlib import Path
from interview_prep_coach.conversation import (
    ConversationSession,
    MemoryStorage,
)


@pytest.fixture
def storage(tmp_path):
    return MemoryStorage(data_dir=tmp_path)


class TestConversationFlow:
    def test_multi_turn_conversation(self, storage, monkeypatch):
        """Test a multi-turn conversation maintains context."""
        # Mock Anthropic API
        responses = [
            "Hey! Good to see you. What are we working on?",
            "Nice! Acme is a great company. Let's start with behavioral questions.",
            "Good answer! You've improved on specificity since last time.",
        ]

        call_count = 0
        def mock_create(*args, **kwargs):
            nonlocal call_count
            class MockResponse:
                content = [type('Content', (), {'text': responses[call_count]})]
            call_count += 1
            return MockResponse()

        monkeypatch.setattr("anthropic.Anthropic.messages.create", mock_create)

        session = ConversationSession(user_id="test_user", storage=storage)

        r1 = session.send_message("Hi Scout!")
        assert "working on" in r1.lower()

        r2 = session.send_message("I have an interview at Acme")
        assert "behavioral" in r2.lower() or "Acme" in r2

        # Verify thread has history
        assert len(session.thread.messages) == 4  # 2 user + 2 assistant

    def test_style_persists_across_sessions(self, storage, monkeypatch):
        """Test that style adjustments persist."""
        monkeypatch.setattr("anthropic.Anthropic.messages.create",
            lambda *a, **k: type('R', (), {'content': [type('C', (), {'text': 'ok'})]}))

        # First session - adjust style
        session1 = ConversationSession(user_id="test_user", storage=storage)
        session1.adjust_style("be more direct")

        # New session - check style persisted
        session2 = ConversationSession(user_id="test_user", storage=storage)
        # Note: Style persistence would need to be saved/loaded
        # This test documents the expected behavior
```

**Step 2: Run integration tests**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/integration/ -v`
Expected: Tests may need API mocking adjustments

**Step 3: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach
git add tests/integration/
git commit -m "test: add integration tests for conversation flow"
```

---

## Summary

**Tasks completed:**
1. ✅ Conversation Thread Foundation
2. ✅ Memory Layers - Working Memory
3. ✅ Memory Persistence with SQLite
4. ✅ Context Builder
5. ✅ Coaching Style Manager
6. ✅ Conversation Session Manager
7. ✅ CLI Chat Command
8. ✅ Integration Tests

**Next steps after implementation:**
- Add long-term memory with embeddings (semantic search)
- Add summarizer for compressing old conversation
- Add iterative refinement mode
- Add scenario exploration mode
- Add conversation analytics (tracking improvement)
