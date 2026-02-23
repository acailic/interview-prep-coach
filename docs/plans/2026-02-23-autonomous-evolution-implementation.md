# Autonomous Evolution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Enable Scout to autonomously learn from conversations through pattern emergence and style drift.

**Architecture:** New `evolution/` module with PatternExtractor, RelationshipTracker, and EffectivenessTracker. Integrated into ConversationSession's send_message() flow with inline AI extraction using Haiku.

**Tech Stack:** Pydantic models, Anthropic Claude API (Haiku for extraction), existing conversation infrastructure.

---

## Task 1: Pattern Extractor Model

**Files:**
- Create: `interview_prep_coach/evolution/__init__.py`
- Create: `interview_prep_coach/evolution/pattern_extractor.py`
- Create: `tests/evolution/__init__.py`
- Create: `tests/evolution/test_pattern_extractor.py`

**Step 1: Write the failing test**

```python
# tests/evolution/test_pattern_extractor.py
"""Tests for pattern extraction from conversations."""

import pytest
from interview_prep_coach.evolution.pattern_extractor import ExtractionResult, PatternExtractor


class TestExtractionResult:
    """Tests for ExtractionResult model."""

    def test_default_values(self):
        """ExtractionResult should have sensible defaults."""
        result = ExtractionResult()
        assert result.weaknesses == []
        assert result.strengths == []
        assert result.engagement_level == "medium"

    def test_with_data(self):
        """ExtractionResult should accept provided values."""
        result = ExtractionResult(
            weaknesses=["struggles with system design"],
            strengths=["good at STAR format"],
            engagement_level="high",
        )
        assert result.weaknesses == ["struggles with system design"]
        assert result.strengths == ["good at STAR format"]
        assert result.engagement_level == "high"


class TestPatternExtractor:
    """Tests for PatternExtractor."""

    def test_extract_returns_result(self):
        """extract() should return an ExtractionResult."""
        extractor = PatternExtractor(api_key="test-key")
        result = extractor.extract(
            user_message="I struggle with system design questions",
            assistant_response="Let's work on that together.",
        )
        assert isinstance(result, ExtractionResult)
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/evolution/test_pattern_extractor.py -v`
Expected: FAIL with module import errors

**Step 3: Write minimal implementation**

```python
# interview_prep_coach/evolution/__init__.py
"""Autonomous evolution capabilities for Scout."""

from .pattern_extractor import ExtractionResult, PatternExtractor

__all__ = ["ExtractionResult", "PatternExtractor"]
```

```python
# interview_prep_coach/evolution/pattern_extractor.py
"""AI-powered pattern extraction from conversations."""

from typing import Optional
from pydantic import BaseModel, Field


EXTRACTION_PROMPT = """Analyze this conversation exchange for interview preparation insights.

User message: {user_message}
Assistant response: {assistant_response}

Extract:
1. Weaknesses: Topics or skills the user struggles with (be specific)
2. Strengths: Techniques or areas where the user shows competence
3. Engagement: How engaged is the user? (high/medium/low)

Respond in JSON format:
{{"weaknesses": ["..."], "strengths": ["..."], "engagement_level": "high|medium|low"}}

If nothing notable found, return empty arrays and "medium" engagement."""


class ExtractionResult(BaseModel):
    """Results of pattern extraction from a conversation exchange."""

    weaknesses: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    engagement_level: str = "medium"


class PatternExtractor:
    """Extracts patterns from conversation using AI."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def extract(self, user_message: str, assistant_response: str) -> ExtractionResult:
        """Extract insights from a conversation exchange."""
        # Placeholder - will be implemented with AI in next task
        return ExtractionResult()
```

**Step 4: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/evolution/test_pattern_extractor.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/evolution/ tests/evolution/ && git commit -m "feat: add PatternExtractor model and ExtractionResult

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Pattern Extractor AI Integration

**Files:**
- Modify: `interview_prep_coach/evolution/pattern_extractor.py`
- Modify: `tests/evolution/test_pattern_extractor.py`

**Step 1: Write the failing test**

```python
# Add to tests/evolution/test_pattern_extractor.py

class TestPatternExtractorAI:
    """Tests for AI-powered extraction."""

    def test_extract_with_real_content(self, monkeypatch):
        """extract() should parse AI response correctly."""
        mock_response = type(
            "MockResponse",
            (),
            {"content": [type("MockContent", (), {"text": '{"weaknesses": ["system design scaling"], "strengths": ["clear communication"], "engagement_level": "high"}'})]},
        )()

        def mock_create(*args, **kwargs):
            return mock_response

        extractor = PatternExtractor(api_key="test-key")
        monkeypatch.setattr(extractor.client.messages, "create", mock_create)

        result = extractor.extract(
            user_message="How do I design a distributed cache?",
            assistant_response="Great question! Let's explore caching strategies...",
        )

        assert "system design scaling" in result.weaknesses
        assert "clear communication" in result.strengths
        assert result.engagement_level == "high"
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/evolution/test_pattern_extractor.py::TestPatternExtractorAI -v`
Expected: FAIL (client not initialized, create not mocked properly)

**Step 3: Write implementation**

```python
# Modify interview_prep_coach/evolution/pattern_extractor.py

import json
from typing import Optional
from pydantic import BaseModel, Field
from anthropic import Anthropic


EXTRACTION_PROMPT = """Analyze this conversation exchange for interview preparation insights.

User message: {user_message}
Assistant response: {assistant_response}

Extract:
1. Weaknesses: Topics or skills the user struggles with (be specific)
2. Strengths: Techniques or areas where the user shows competence
3. Engagement: How engaged is the user? (high/medium/low)

Respond in JSON format only, no other text:
{{"weaknesses": ["..."], "strengths": ["..."], "engagement_level": "high|medium|low"}}

If nothing notable found, return empty arrays and "medium" engagement."""


class ExtractionResult(BaseModel):
    """Results of pattern extraction from a conversation exchange."""

    weaknesses: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    engagement_level: str = "medium"


class PatternExtractor:
    """Extracts patterns from conversation using AI."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()

    def extract(self, user_message: str, assistant_response: str) -> ExtractionResult:
        """Extract insights from a conversation exchange using AI."""
        prompt = EXTRACTION_PROMPT.format(
            user_message=user_message,
            assistant_response=assistant_response,
        )

        response = self.client.messages.create(
            model="claude-haiku-3-5-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            data = json.loads(response.content[0].text)
            return ExtractionResult(
                weaknesses=data.get("weaknesses", []),
                strengths=data.get("strengths", []),
                engagement_level=data.get("engagement_level", "medium"),
            )
        except (json.JSONDecodeError, KeyError):
            return ExtractionResult()
```

**Step 4: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/evolution/test_pattern_extractor.py -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/evolution/pattern_extractor.py tests/evolution/test_pattern_extractor.py && git commit -m "feat: add AI-powered pattern extraction

Uses Claude Haiku to extract weaknesses, strengths, and engagement from conversation exchanges.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Relationship Tracker

**Files:**
- Create: `interview_prep_coach/evolution/relationship_tracker.py`
- Create: `tests/evolution/test_relationship_tracker.py`

**Step 1: Write the failing test**

```python
# tests/evolution/test_relationship_tracker.py
"""Tests for relationship tracking."""

import pytest
from interview_prep_coach.evolution.relationship_tracker import RelationshipTracker


class TestRelationshipTracker:
    """Tests for relationship phase tracking."""

    def test_initial_state(self):
        """New tracker should start at formal phase."""
        tracker = RelationshipTracker()
        assert tracker.total_exchanges == 0
        assert tracker.relationship_phase == "formal"

    def test_record_exchange(self):
        """Recording exchange should increment count."""
        tracker = RelationshipTracker()
        tracker.record_exchange()
        assert tracker.total_exchanges == 1

    def test_phase_transition_to_familiar(self):
        """Should transition to familiar after 10 exchanges."""
        tracker = RelationshipTracker()
        for _ in range(10):
            tracker.record_exchange()
        assert tracker.relationship_phase == "familiar"

    def test_phase_transition_to_trusted(self):
        """Should transition to trusted after 50 exchanges."""
        tracker = RelationshipTracker()
        for _ in range(50):
            tracker.record_exchange()
        assert tracker.relationship_phase == "trusted"

    def test_get_phase_modifier_formal(self):
        """Formal phase should have professional modifier."""
        tracker = RelationshipTracker()
        assert "professional" in tracker.get_phase_modifier().lower()

    def test_get_phase_modifier_familiar(self):
        """Familiar phase should have warm modifier."""
        tracker = RelationshipTracker()
        tracker.relationship_phase = "familiar"
        assert "warm" in tracker.get_phase_modifier().lower()

    def test_get_phase_modifier_trusted(self):
        """Trusted phase should have candid modifier."""
        tracker = RelationshipTracker()
        tracker.relationship_phase = "trusted"
        assert "candid" in tracker.get_phase_modifier().lower()
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/evolution/test_relationship_tracker.py -v`
Expected: FAIL with module import errors

**Step 3: Write implementation**

```python
# interview_prep_coach/evolution/relationship_tracker.py
"""Relationship phase tracking for style drift."""

from pydantic import BaseModel, Field


class RelationshipTracker(BaseModel):
    """Tracks relationship depth for style drift."""

    total_exchanges: int = 0
    relationship_phase: str = "formal"  # formal → familiar → trusted

    def record_exchange(self) -> None:
        """Record a conversation exchange and update phase if needed."""
        self.total_exchanges += 1
        self._update_phase()

    def _update_phase(self) -> None:
        """Update relationship phase based on exchange count."""
        if self.total_exchanges >= 51:
            self.relationship_phase = "trusted"
        elif self.total_exchanges >= 11:
            self.relationship_phase = "familiar"
        else:
            self.relationship_phase = "formal"

    def get_phase_modifier(self) -> str:
        """Get system prompt modifier for current phase."""
        modifiers = {
            "formal": "Maintain a professional, encouraging tone with this new learner.",
            "familiar": "You know this learner well. Be warm and personable in your coaching.",
            "trusted": "You are a trusted coach with a strong relationship. Be candid and personal when helpful.",
        }
        return modifiers.get(self.relationship_phase, modifiers["formal"])
```

**Step 4: Update __init__.py**

```python
# Modify interview_prep_coach/evolution/__init__.py
"""Autonomous evolution capabilities for Scout."""

from .pattern_extractor import ExtractionResult, PatternExtractor
from .relationship_tracker import RelationshipTracker

__all__ = ["ExtractionResult", "PatternExtractor", "RelationshipTracker"]
```

**Step 5: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/evolution/test_relationship_tracker.py -v`
Expected: PASS (8 tests)

**Step 6: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/evolution/ tests/evolution/test_relationship_tracker.py && git commit -m "feat: add RelationshipTracker for familiarity phases

Tracks formal → familiar → trusted progression based on exchange count.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Effectiveness Tracker

**Files:**
- Create: `interview_prep_coach/evolution/effectiveness.py`
- Create: `tests/evolution/test_effectiveness.py`

**Step 1: Write the failing test**

```python
# tests/evolution/test_effectiveness.py
"""Tests for effectiveness tracking."""

import pytest
from interview_prep_coach.evolution.effectiveness import EffectivenessTracker


class TestEffectivenessTracker:
    """Tests for style effectiveness tracking."""

    def test_initial_state(self):
        """New tracker should have empty outcomes."""
        tracker = EffectivenessTracker()
        assert tracker.style_outcomes == {}

    def test_record_high_engagement(self):
        """High engagement should add positive score."""
        tracker = EffectivenessTracker()
        tracker.record_outcome("direct:high", "high")
        assert tracker.style_outcomes["direct:high"] == 2

    def test_record_medium_engagement(self):
        """Medium engagement should add zero."""
        tracker = EffectivenessTracker()
        tracker.record_outcome("direct:high", "medium")
        assert tracker.style_outcomes["direct:high"] == 0

    def test_record_low_engagement(self):
        """Low engagement should subtract."""
        tracker = EffectivenessTracker()
        tracker.record_outcome("direct:high", "low")
        assert tracker.style_outcomes["direct:high"] == -1

    def test_cumulative_scoring(self):
        """Scores should accumulate."""
        tracker = EffectivenessTracker()
        tracker.record_outcome("collaborative:medium", "high")
        tracker.record_outcome("collaborative:medium", "high")
        tracker.record_outcome("collaborative:medium", "low")
        assert tracker.style_outcomes["collaborative:medium"] == 3  # 2 + 2 - 1

    def test_get_recommended_style_insufficient_data(self):
        """Should return None with insufficient samples."""
        tracker = EffectivenessTracker()
        tracker.record_outcome("direct:high", "high")
        result = tracker.get_recommended_style()
        assert result is None  # Only 1 sample, need 5+

    def test_get_recommended_style_sufficient_data(self):
        """Should return top style with sufficient samples."""
        tracker = EffectivenessTracker()
        # Record 5 high-engagement outcomes for collaborative
        for _ in range(5):
            tracker.record_outcome("collaborative:medium", "high")
        # Record 5 low-engagement outcomes for directive
        for _ in range(5):
            tracker.record_outcome("direct:high", "low")

        result = tracker.get_recommended_style()
        assert result == "collaborative:medium"
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/evolution/test_effectiveness.py -v`
Expected: FAIL with module import errors

**Step 3: Write implementation**

```python
# interview_prep_coach/evolution/effectiveness.py
"""Style effectiveness tracking for drift."""

from typing import Optional
from pydantic import BaseModel, Field


class EffectivenessTracker(BaseModel):
    """Tracks which style combinations lead to better engagement."""

    style_outcomes: dict[str, int] = Field(default_factory=dict)
    _sample_counts: dict[str, int] = {}

    def record_outcome(self, style: str, engagement: str) -> None:
        """Record engagement outcome for a style configuration.

        Args:
            style: Style configuration string (e.g., "collaborative:medium")
            engagement: Engagement level ("high", "medium", "low")
        """
        scores = {"high": 2, "medium": 0, "low": -1}
        delta = scores.get(engagement, 0)

        if style not in self.style_outcomes:
            self.style_outcomes[style] = 0
        self.style_outcomes[style] += delta

        # Track sample count separately (not persisted)
        if not hasattr(self, "_sample_counts"):
            self._sample_counts = {}
        self._sample_counts[style] = self._sample_counts.get(style, 0) + 1

    def get_recommended_style(self, min_samples: int = 5) -> Optional[str]:
        """Get the style with highest effectiveness score.

        Args:
            min_samples: Minimum samples required for recommendation

        Returns:
            Style string with highest score, or None if insufficient data
        """
        if not hasattr(self, "_sample_counts"):
            return None

        qualified_styles = [
            style for style, count in self._sample_counts.items()
            if count >= min_samples and style in self.style_outcomes
        ]

        if not qualified_styles:
            return None

        return max(qualified_styles, key=lambda s: self.style_outcomes.get(s, 0))
```

**Step 4: Update __init__.py**

```python
# Modify interview_prep_coach/evolution/__init__.py
"""Autonomous evolution capabilities for Scout."""

from .pattern_extractor import ExtractionResult, PatternExtractor
from .relationship_tracker import RelationshipTracker
from .effectiveness import EffectivenessTracker

__all__ = [
    "ExtractionResult",
    "PatternExtractor",
    "RelationshipTracker",
    "EffectivenessTracker",
]
```

**Step 5: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/evolution/test_effectiveness.py -v`
Expected: PASS (7 tests)

**Step 6: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/evolution/ tests/evolution/test_effectiveness.py && git commit -m "feat: add EffectivenessTracker for style drift

Tracks which style combinations correlate with user engagement.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Evolution State Model

**Files:**
- Create: `interview_prep_coach/evolution/state.py`
- Modify: `interview_prep_coach/evolution/__init__.py`
- Create: `tests/evolution/test_state.py`

**Step 1: Write the failing test**

```python
# tests/evolution/test_state.py
"""Tests for evolution state."""

from interview_prep_coach.evolution.state import EvolutionState
from interview_prep_coach.evolution.relationship_tracker import RelationshipTracker
from interview_prep_coach.evolution.effectiveness import EffectivenessTracker


class TestEvolutionState:
    """Tests for combined evolution state."""

    def test_default_state(self):
        """EvolutionState should have default components."""
        state = EvolutionState()
        assert isinstance(state.relationship, RelationshipTracker)
        assert isinstance(state.effectiveness, EffectivenessTracker)

    def test_record_exchange(self):
        """record_exchange should delegate to relationship tracker."""
        state = EvolutionState()
        state.record_exchange()
        assert state.relationship.total_exchanges == 1

    def test_record_style_outcome(self):
        """record_style_outcome should delegate to effectiveness tracker."""
        state = EvolutionState()
        state.record_style_outcome("collaborative", "high")
        assert "collaborative" in state.effectiveness.style_outcomes
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/evolution/test_state.py -v`
Expected: FAIL with module import errors

**Step 3: Write implementation**

```python
# interview_prep_coach/evolution/state.py
"""Combined evolution state for persistence."""

from pydantic import BaseModel, Field

from .relationship_tracker import RelationshipTracker
from .effectiveness import EffectivenessTracker


class EvolutionState(BaseModel):
    """Combined state for all evolution components."""

    relationship: RelationshipTracker = Field(default_factory=RelationshipTracker)
    effectiveness: EffectivenessTracker = Field(default_factory=EffectivenessTracker)

    def record_exchange(self) -> None:
        """Record a conversation exchange."""
        self.relationship.record_exchange()

    def record_style_outcome(self, style: str, engagement: str) -> None:
        """Record style effectiveness outcome."""
        self.effectiveness.record_outcome(style, engagement)
```

**Step 4: Update __init__.py**

```python
# Modify interview_prep_coach/evolution/__init__.py
"""Autonomous evolution capabilities for Scout."""

from .pattern_extractor import ExtractionResult, PatternExtractor
from .relationship_tracker import RelationshipTracker
from .effectiveness import EffectivenessTracker
from .state import EvolutionState

__all__ = [
    "ExtractionResult",
    "PatternExtractor",
    "RelationshipTracker",
    "EffectivenessTracker",
    "EvolutionState",
]
```

**Step 5: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/evolution/test_state.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/evolution/ tests/evolution/test_state.py && git commit -m "feat: add EvolutionState for combined state management

Combines relationship and effectiveness tracking into single state object.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Integrate Evolution into Session

**Files:**
- Modify: `interview_prep_coach/conversation/session.py`
- Modify: `interview_prep_coach/conversation/storage.py`
- Modify: `tests/conversation/test_session.py` (or create if needed)

**Step 1: Write the failing test**

```python
# Add to tests/conversation/test_session.py or create new file
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
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_session_evolution.py -v`
Expected: FAIL with attribute errors

**Step 3: Update storage for evolution state**

```python
# Modify interview_prep_coach/conversation/storage.py
# Add these methods to MemoryStorage class:

    def save_evolution_state(self, user_id: str, state: "EvolutionState") -> None:
        """Save evolution state to disk."""
        path = self.data_dir / "evolution" / f"{user_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(state.model_dump_json(indent=2))

    def load_evolution_state(self, user_id: str) -> Optional["EvolutionState"]:
        """Load evolution state from disk."""
        path = self.data_dir / "evolution" / f"{user_id}.json"
        if not path.exists():
            return None

        from interview_prep_coach.evolution.state import EvolutionState
        return EvolutionState.model_validate_json(path.read_text())
```

**Step 4: Update session to integrate evolution**

```python
# Modify interview_prep_coach/conversation/session.py
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

    def _save_state(self) -> None:
        self.storage.save_thread(self.thread)
        self.storage.save_working_memory(self.user_id, self.working_memory)
        self.storage.save_evolution_state(self.user_id, self.evolution_state)
```

**Step 5: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_session_evolution.py -v`
Expected: PASS (5 tests)

**Step 6: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/conversation/session.py interview_prep_coach/conversation/storage.py tests/conversation/ && git commit -m "feat: integrate evolution into conversation session

- Add pattern extraction after each message
- Record exchanges and engagement
- Apply style drift every 10 exchanges
- Persist evolution state

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Run Full Test Suite

**Step 1: Run all tests**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/ -v`
Expected: All tests pass

**Step 2: Fix any failures**

If tests fail, fix them before proceeding.

**Step 3: Commit any fixes**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add -A && git commit -m "fix: resolve test failures

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Summary

After completing all tasks:
- Pattern emergence extracts insights from each conversation
- Relationship tracker progresses formal → familiar → trusted
- Effectiveness tracker learns which styles work best
- Style drift nudges coaching style every 10 exchanges
- All state persists across sessions

**Files created:**
- `interview_prep_coach/evolution/__init__.py`
- `interview_prep_coach/evolution/pattern_extractor.py`
- `interview_prep_coach/evolution/relationship_tracker.py`
- `interview_prep_coach/evolution/effectiveness.py`
- `interview_prep_coach/evolution/state.py`
- `tests/evolution/__init__.py`
- `tests/evolution/test_pattern_extractor.py`
- `tests/evolution/test_relationship_tracker.py`
- `tests/evolution/test_effectiveness.py`
- `tests/evolution/test_state.py`
- `tests/conversation/test_session_evolution.py`

**Files modified:**
- `interview_prep_coach/conversation/session.py`
- `interview_prep_coach/conversation/storage.py`
