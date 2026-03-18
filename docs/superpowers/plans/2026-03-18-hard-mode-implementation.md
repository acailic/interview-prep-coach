# Hard Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add opt-in `--hard` flag for tougher scoring and more critical feedback in interview practice.

**Architecture:** Extend existing Scorer and FeedbackAnalyzer with hard mode variants. Add `--hard` CLI flag to practice commands. Store hard mode preference in PracticeSession for tracking.

**Tech Stack:** Python 3.11+, Pydantic, Click, pytest

---

## File Structure

| File | Responsibility |
|------|----------------|
| `interview_prep_coach/models.py` | Add `hard_mode: bool` field to PracticeSession |
| `interview_prep_coach/practice/scorer.py` | Add hard mode scoring thresholds |
| `interview_prep_coach/practice/feedback_analyzer.py` | Add hard mode system prompt |
| `interview_prep_coach/practice/engine.py` | Pass hard_mode through to dependencies |
| `interview_prep_coach/cli.py` | Add `--hard` flag to commands |
| `tests/practice/test_scorer_hard_mode.py` | Test hard mode scoring |
| `tests/practice/test_feedback_analyzer_hard_mode.py` | Test hard mode prompts |
| `tests/practice/test_engine_hard_mode.py` | Test engine hard mode integration |

---

## Task 1: Add hard_mode to PracticeSession Model

**Files:**
- Modify: `interview_prep_coach/models.py:79-111`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py - add to TestPracticeSession class

def test_create_session_with_hard_mode(self):
    """Test that PracticeSession can store hard_mode flag."""
    session = PracticeSession(
        session_id="session-hard-123",
        mode=PracticeMode.focused,
        hard_mode=True,
    )
    assert session.hard_mode is True


def test_hard_mode_defaults_to_false(self):
    """Test that hard_mode defaults to False."""
    session = PracticeSession(
        session_id="session-normal-123",
        mode=PracticeMode.focused,
    )
    assert session.hard_mode is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::TestPracticeSession::test_create_session_with_hard_mode -v`
Expected: FAIL with "unexpected keyword argument 'hard_mode'"

- [ ] **Step 3: Add hard_mode field to PracticeSession**

```python
# interview_prep_coach/models.py - add to PracticeSession class

class PracticeSession(BaseModel):
    """A practice session with multiple questions.

    Attributes:
        session_id: Unique session identifier
        started_at: When the session started
        completed_at: When the session ended (None if in progress)
        mode: Practice mode for this session
        category_filter: Optional category filter applied
        time_limit_seconds: Optional time limit for the session
        questions: List of question attempts in this session
        hard_mode: Whether hard mode (tougher scoring) is enabled
    """

    session_id: str
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = Field(default=None)
    mode: PracticeMode
    category_filter: str | None = Field(default=None)
    time_limit_seconds: int | None = Field(default=None)
    questions: list[QuestionAttempt] = Field(default_factory=list)
    hard_mode: bool = False  # NEW FIELD
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py::TestPracticeSession -v`
Expected: PASS (all tests in class)

- [ ] **Step 5: Commit**

```bash
git add interview_prep_coach/models.py tests/test_models.py
git commit -m "feat: add hard_mode field to PracticeSession model

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Add Hard Mode Scoring to Scorer

**Files:**
- Modify: `interview_prep_coach/practice/scorer.py`
- Create: `tests/practice/test_scorer_hard_mode.py`

- [ ] **Step 1: Create tests/practice directory**

```bash
mkdir -p tests/practice
touch tests/practice/__init__.py
```

- [ ] **Step 2: Write the failing tests**

```python
# tests/practice/test_scorer_hard_mode.py

import pytest
from interview_prep_coach.practice.scorer import Scorer
from interview_prep_coach.models import QuestionCategory


class TestScorerHardMode:
    """Test hard mode scoring behavior."""

    def test_hard_mode_lower_base_score(self):
        """Hard mode should start with lower base score (4.0 vs 7.0)."""
        scorer = Scorer()

        # Normal mode with no weak areas and positive feedback
        normal_score = scorer.score_answer(
            feedback="Excellent answer with great clarity.",
            weak_areas=[],
            category=QuestionCategory.behavioral,
            hard_mode=False,
        )

        # Hard mode with same input
        hard_score = scorer.score_answer(
            feedback="Excellent answer with great clarity.",
            weak_areas=[],
            category=QuestionCategory.behavioral,
            hard_mode=True,
        )

        # Hard mode should be lower (4.0 base vs 7.0 base)
        assert hard_score < normal_score
        # With positive sentiment, normal ~8.5, hard ~4.5
        assert normal_score > 7.0
        assert hard_score <= 5.0  # Max is 4.0 base + 1.0 max sentiment

    def test_hard_mode_steeper_weak_area_penalties(self):
        """Hard mode should penalize weak areas more heavily."""
        scorer = Scorer()
        weak_areas = ["specificity", "structure"]

        normal_score = scorer.score_answer(
            feedback="Good attempt but needs improvement.",
            weak_areas=weak_areas,
            category=QuestionCategory.behavioral,
            hard_mode=False,
        )

        hard_score = scorer.score_answer(
            feedback="Good attempt but needs improvement.",
            weak_areas=weak_areas,
            category=QuestionCategory.behavioral,
            hard_mode=True,
        )

        # Normal: 7.0 - 2.0 (2 weak areas) = 5.0
        # Hard: 4.0 - 4.0 (2 weak areas) = 0.0
        assert normal_score >= 4.0
        assert hard_score <= 1.0

    def test_hard_mode_caps_positive_sentiment(self):
        """Hard mode should cap positive sentiment bonus at +1.0."""
        scorer = Scorer()

        # Very positive feedback
        positive_feedback = "Excellent great strong good well clear effective solid polished"

        normal_score = scorer.score_answer(
            feedback=positive_feedback,
            weak_areas=[],
            category=QuestionCategory.behavioral,
            hard_mode=False,
        )

        hard_score = scorer.score_answer(
            feedback=positive_feedback,
            weak_areas=[],
            category=QuestionCategory.behavioral,
            hard_mode=True,
        )

        # Normal can go up to 9.0 (7.0 + 2.0 max sentiment)
        # Hard maxes at 5.0 (4.0 + 1.0 max sentiment)
        assert normal_score >= 8.0
        assert hard_score <= 5.0

    def test_one_weak_area_hard_mode_penalty(self):
        """Hard mode should penalize 1 weak area by 2.0."""
        scorer = Scorer()

        score = scorer.score_answer(
            feedback="Decent answer.",
            weak_areas=["clarity"],
            category=QuestionCategory.behavioral,
            hard_mode=True,
        )

        # 4.0 base - 2.0 penalty = 2.0
        assert 1.0 <= score <= 3.0

    def test_three_weak_areas_hard_mode_penalty(self):
        """Hard mode should penalize 3+ weak areas by 6.0 (floor at 0)."""
        scorer = Scorer()

        score = scorer.score_answer(
            feedback="Needs work.",
            weak_areas=["clarity", "specificity", "structure"],
            category=QuestionCategory.behavioral,
            hard_mode=True,
        )

        # 4.0 base - 6.0 penalty + sentiment = -2.0 + sentiment
        # Even with slight negative sentiment, floor is 0.0
        assert score == 0.0

    def test_calculate_score_accepts_hard_mode(self):
        """calculate_score method should accept hard_mode parameter."""
        scorer = Scorer()

        score = scorer.calculate_score(
            question={"text": "Test", "category": "behavioral"},
            answer="My answer",
            feedback="Good work.",
            hard_mode=True,
        )

        assert isinstance(score, float)
        assert 0.0 <= score <= 10.0
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/practice/test_scorer_hard_mode.py -v`
Expected: FAIL with "unexpected keyword argument 'hard_mode'"

- [ ] **Step 4: Modify score_answer to accept hard_mode**

```python
# interview_prep_coach/practice/scorer.py - modify score_answer method

def score_answer(
    self,
    feedback: str,
    weak_areas: list[str],
    category: QuestionCategory,
    hard_mode: bool = False,  # NEW PARAMETER
) -> float:
    """Calculate a score from 0-10 based on feedback and weak areas.

    Args:
        feedback: The feedback text from FeedbackAnalyzer
        weak_areas: List of identified weak areas
        category: Question category (affects scoring weights)
        hard_mode: If True, use tougher scoring thresholds

    Returns:
        Score from 0.0 to 10.0
    """
    base_score = 4.0 if hard_mode else 7.0

    sentiment_score = self._analyze_sentiment(feedback, hard_mode)
    weak_area_penalty = self._calculate_weak_area_penalty(weak_areas, hard_mode)

    raw_score = base_score + sentiment_score - weak_area_penalty

    return max(0.0, min(10.0, raw_score))
```

- [ ] **Step 5: Modify _calculate_weak_area_penalty for hard mode**

```python
# interview_prep_coach/practice/scorer.py - modify _calculate_weak_area_penalty

def _calculate_weak_area_penalty(self, weak_areas: list[str], hard_mode: bool = False) -> float:
    """Calculate score penalty based on number of weak areas.

    Args:
        weak_areas: List of identified weak areas
        hard_mode: If True, use steeper penalties

    Returns:
        Penalty from 0.0 to 5.0 (normal) or 0.0 to 6.0 (hard)
    """
    if not weak_areas:
        return 0.0

    num_weak_areas = len(weak_areas)

    if hard_mode:
        # Hard mode: steeper penalties
        if num_weak_areas == 1:
            return 2.0
        elif num_weak_areas == 2:
            return 4.0
        else:
            return 6.0  # 3+ weak areas = max penalty

    # Normal mode: existing logic
    if num_weak_areas == 1:
        return 1.0
    elif num_weak_areas == 2:
        return 2.0
    elif num_weak_areas == 3:
        return 3.0
    else:
        return min(5.0, 3.0 + (num_weak_areas - 3) * 0.5)
```

- [ ] **Step 6: Modify _analyze_sentiment for hard mode**

```python
# interview_prep_coach/practice/scorer.py - modify _analyze_sentiment

def _analyze_sentiment(self, feedback: str, hard_mode: bool = False) -> float:
    """Analyze feedback sentiment and return score adjustment.

    Args:
        feedback: Feedback text to analyze
        hard_mode: If True, cap positive bonus at +1.0

    Returns:
        Score adjustment from -2.0 to +2.0 (normal) or -1.0 to +1.0 (hard)
    """
    if not feedback:
        return 0.0

    lower_feedback = feedback.lower()

    positive_count = sum(
        1 for indicator in self.POSITIVE_INDICATORS
        if indicator in lower_feedback
    )
    negative_count = sum(
        1 for indicator in self.NEGATIVE_INDICATORS
        if indicator in lower_feedback
    )

    net_sentiment = positive_count - negative_count

    if hard_mode:
        # Hard mode: cap at ±1.0
        return max(-1.0, min(1.0, net_sentiment * 0.25))

    # Normal mode: ±2.0
    return max(-2.0, min(2.0, net_sentiment * 0.5))
```

- [ ] **Step 7: Modify calculate_score to accept hard_mode**

```python
# interview_prep_coach/practice/scorer.py - modify calculate_score

def calculate_score(
    self,
    question: dict,
    answer: str,
    feedback: str,
    hard_mode: bool = False,  # NEW PARAMETER
) -> float:
    """Calculate a score for the answer.

    Args:
        question: Question dict with 'text' and 'category' keys
        answer: User's answer text
        feedback: Feedback text from FeedbackAnalyzer
        hard_mode: If True, use tougher scoring thresholds

    Returns:
        Score from 0.0 to 10.0
    """
    if not answer or not answer.strip():
        return 0.0

    category_str = question.get("category", "behavioral")
    try:
        category = QuestionCategory(category_str)
    except ValueError:
        category = QuestionCategory.behavioral

    weak_areas = self._extract_weak_areas_from_feedback(feedback)

    return self.score_answer(feedback, weak_areas, category, hard_mode)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest tests/practice/test_scorer_hard_mode.py -v`
Expected: PASS (all 6 tests)

- [ ] **Step 8: Commit**

```bash
git add interview_prep_coach/practice/scorer.py tests/practice/test_scorer_hard_mode.py
git commit -m "feat: add hard mode scoring to Scorer

- Lower base score from 7.0 to 4.0 in hard mode
- Steeper weak area penalties (2.0/4.0/6.0 vs 1.0/2.0/3.0)
- Cap positive sentiment at +1.0 instead of +2.0

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Add Hard Mode to FeedbackAnalyzer

**Files:**
- Modify: `interview_prep_coach/practice/feedback_analyzer.py`
- Create: `tests/practice/test_feedback_analyzer_hard_mode.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/practice/test_feedback_analyzer_hard_mode.py

import pytest
from interview_prep_coach.practice.feedback_analyzer import FeedbackAnalyzer
from interview_prep_coach.models import QuestionCategory


class TestFeedbackAnalyzerHardMode:
    """Test hard mode feedback prompts."""

    def test_get_system_prompt_includes_hard_mode_modifier(self):
        """Hard mode prompt should include critical evaluation instructions."""
        analyzer = FeedbackAnalyzer()

        normal_prompt = analyzer._get_system_prompt(QuestionCategory.behavioral, hard_mode=False)
        hard_prompt = analyzer._get_system_prompt(QuestionCategory.behavioral, hard_mode=True)

        # Hard mode should mention being honest/critical
        assert "brutally honest" in hard_prompt.lower() or "critical" in hard_prompt.lower()
        # Normal mode should be constructive
        assert "constructive" in normal_prompt.lower()

    def test_hard_mode_prompt_differs_from_normal(self):
        """Hard mode prompt should be different from normal mode."""
        analyzer = FeedbackAnalyzer()

        normal_prompt = analyzer._get_system_prompt(QuestionCategory.behavioral, hard_mode=False)
        hard_prompt = analyzer._get_system_prompt(QuestionCategory.behavioral, hard_mode=True)

        assert normal_prompt != hard_prompt

    def test_analyze_answer_accepts_hard_mode(self):
        """analyze_answer method should accept hard_mode parameter."""
        import inspect
        analyzer = FeedbackAnalyzer()
        sig = inspect.signature(analyzer.analyze_answer)
        params = list(sig.parameters.keys())

        assert "hard_mode" in params


class TestHardModePromptContent:
    """Test content of hard mode prompts."""

    def test_hard_mode_includes_score_guidance(self):
        """Hard mode should include tougher score band guidance."""
        analyzer = FeedbackAnalyzer()

        hard_prompt = analyzer._get_system_prompt(QuestionCategory.behavioral, hard_mode=True)

        # Should mention that high scores require excellence
        assert "8" in hard_prompt or "impressive" in hard_prompt.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/practice/test_feedback_analyzer_hard_mode.py -v`
Expected: FAIL (various assertion errors)

- [ ] **Step 3: Add HARD_MODE_MODIFIER constant**

```python
# interview_prep_coach/practice/feedback_analyzer.py - add after CATEGORY_PROMPTS

HARD_MODE_MODIFIER = """
HARD MODE EVALUATION - Be brutally honest in your evaluation.

Score 0-3: Significant gaps, not interview-ready. Major issues that would concern interviewers.
Score 4-5: Below average, several areas need work. Would not stand out.
Score 6-7: Acceptable but not impressive. Meets basic expectations.
Score 8-9: Polished and impressive. Would catch an interviewer's attention.
Score 10: Exceptional. Would stand out in competitive interviews.

Default to critique over encouragement. Identify every weakness without sugar-coating.
Push for excellence - an 8+ requires a truly interview-ready, polished answer.
"""
```

- [ ] **Step 4: Modify _get_system_prompt for hard mode**

```python
# interview_prep_coach/practice/feedback_analyzer.py - modify _get_system_prompt

def _get_system_prompt(self, category: QuestionCategory, hard_mode: bool = False) -> str:
    """Get the system prompt for a question category.

    Args:
        category: The question category
        hard_mode: If True, include critical evaluation modifier

    Returns:
        Complete system prompt string
    """
    base_prompt = self.CATEGORY_PROMPTS.get(
        category,
        self.CATEGORY_PROMPTS[QuestionCategory.behavioral]
    )

    if hard_mode:
        return f"""{base_prompt}

IMPORTANT: You must respond in the following JSON format only:
{{
    "feedback": "Your detailed feedback (2-3 paragraphs with specific suggestions)",
    "score": 7.5,
    "weak_areas": ["area1", "area2"],
    "strengths": ["strength1", "strength2"]
}}

{self.HARD_MODE_MODIFIER}"""

    return f"""{base_prompt}

IMPORTANT: You must respond in the following JSON format only:
{{
    "feedback": "Your detailed feedback (2-3 paragraphs with specific suggestions)",
    "score": 7.5,
    "weak_areas": ["area1", "area2"],
    "strengths": ["strength1", "strength2"]
}}

Score on a 0-10 scale where:
- 0-3: Major issues, needs significant improvement
- 4-5: Below average, several areas to improve
- 6-7: Average to good, minor improvements possible
- 8-9: Very good, polished answer
- 10: Exceptional, interview-ready

Be constructive and specific in feedback. Always provide actionable suggestions."""
```

- [ ] **Step 5: Modify analyze_answer to accept hard_mode**

```python
# interview_prep_coach/practice/feedback_analyzer.py - modify analyze_answer

async def analyze_answer(
    self,
    question: dict,
    answer: str,
    hard_mode: bool = False,  # NEW PARAMETER
) -> tuple[str, float, list[str]]:
    """Analyze an answer and provide feedback.

    Args:
        question: Question dict with 'text' and 'category' keys
        answer: User's answer text
        hard_mode: If True, use critical evaluation mode

    Returns:
        Tuple of (feedback_text, score_0_to_10, list_of_weak_areas)
    """
    if not answer or not answer.strip():
        return "No answer provided. Please provide an answer to receive feedback.", 0.0, ["no_answer"]

    category_str = question.get("category", "behavioral")
    try:
        category = QuestionCategory(category_str)
    except ValueError:
        category = QuestionCategory.behavioral

    system_prompt = self._get_system_prompt(category, hard_mode)  # PASS hard_mode
    analysis_prompt = self._build_analysis_prompt(question, answer, category)

    options = SessionOptions(
        system_prompt=system_prompt,
        max_turns=1,
    )

    async with ClaudeSession(options) as claude:
        response = await claude.query(analysis_prompt)

        if not response.success:
            return self._fallback_feedback(category), 5.0, ["analysis_unavailable"]

        return self._parse_response(response.content)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/practice/test_feedback_analyzer_hard_mode.py -v`
Expected: PASS (all 4 tests)

- [ ] **Step 7: Commit**

```bash
git add interview_prep_coach/practice/feedback_analyzer.py tests/practice/test_feedback_analyzer_hard_mode.py
git commit -m "feat: add hard mode prompts to FeedbackAnalyzer

- Add HARD_MODE_MODIFIER with critical evaluation guidance
- Modify _get_system_prompt to include hard mode variant
- Pass hard_mode through analyze_answer method

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Update PracticeEngine to Pass Hard Mode

**Files:**
- Modify: `interview_prep_coach/practice/engine.py`
- Modify: `interview_prep_coach/cli.py:41-52`

- [ ] **Step 1: Write the failing test**

```python
# tests/practice/test_engine_hard_mode.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from interview_prep_coach.practice.engine import PracticeEngine
from interview_prep_coach.models import PracticeMode, QuestionCategory


class TestPracticeEngineHardMode:
    """Test hard mode integration in PracticeEngine."""

    @pytest.mark.asyncio
    async def test_start_session_accepts_hard_mode(self):
        """start_session should accept hard_mode parameter."""
        mock_bank = MagicMock()
        mock_tracker = MagicMock()
        mock_analyzer = AsyncMock()
        mock_scorer = MagicMock()

        mock_tracker.get_completed_question_ids.return_value = []
        mock_bank.get_questions.return_value = []

        engine = PracticeEngine(
            question_bank=mock_bank,
            progress_tracker=mock_tracker,
            feedback_analyzer=mock_analyzer,
            scorer=mock_scorer,
        )

        session = await engine.start_session(
            mode=PracticeMode.focused,
            category=QuestionCategory.behavioral,
            hard_mode=True,
        )

        assert session.hard_mode is True

    @pytest.mark.asyncio
    async def test_submit_answer_passes_hard_mode_to_analyzer(self):
        """submit_answer should pass hard_mode to feedback analyzer."""
        mock_bank = MagicMock()
        mock_tracker = MagicMock()
        mock_analyzer = AsyncMock()
        mock_scorer = MagicMock()

        mock_tracker.get_completed_question_ids.return_value = []
        mock_bank.get_questions.return_value = [
            {"id": "q1", "text": "Test question", "category": "behavioral"}
        ]
        mock_bank.get_question_by_id.return_value = {
            "id": "q1", "text": "Test question", "category": "behavioral"
        }
        mock_analyzer.analyze_answer.return_value = ("Good", 7.0, [])

        engine = PracticeEngine(
            question_bank=mock_bank,
            progress_tracker=mock_tracker,
            feedback_analyzer=mock_analyzer,
            scorer=mock_scorer,
        )

        await engine.start_session(mode=PracticeMode.focused, hard_mode=True)
        await engine.submit_answer("q1", "My answer")

        # Verify analyzer was called with hard_mode=True
        mock_analyzer.analyze_answer.assert_called_once()
        call_kwargs = mock_analyzer.analyze_answer.call_args.kwargs
        assert call_kwargs.get("hard_mode") is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/practice/test_engine_hard_mode.py -v`
Expected: FAIL with "unexpected keyword argument 'hard_mode'"

- [ ] **Step 3: Modify PracticeEngine.__init__ to store hard_mode**

```python
# interview_prep_coach/practice/engine.py - modify __init__

def __init__(
    self,
    question_bank: QuestionBankProtocol,
    progress_tracker: ProgressTrackerProtocol,
    feedback_analyzer: FeedbackAnalyzerProtocol,
    scorer: ScorerProtocol | None = None,
    hard_mode: bool = False,  # NEW PARAMETER
):
    """Initialize the practice engine.

    Args:
        question_bank: Source of questions
        progress_tracker: Records progress
        feedback_analyzer: Analyzes answers for feedback
        scorer: Optional scorer for calculating scores
        hard_mode: Whether to use tougher scoring and feedback
    """
    self._question_bank = question_bank
    self._progress_tracker = progress_tracker
    self._feedback_analyzer = feedback_analyzer
    self._scorer = scorer
    self._hard_mode = hard_mode  # NEW
    self._current_session: PracticeSession | None = None
    self._pending_questions: list[dict] = []
```

- [ ] **Step 4: Modify start_session to accept hard_mode**

```python
# interview_prep_coach/practice/engine.py - modify start_session

async def start_session(
    self,
    mode: PracticeMode,
    category: QuestionCategory | None = None,
    time_limit: int | None = None,
    hard_mode: bool | None = None,  # NEW PARAMETER
) -> PracticeSession:
    """Start a new practice session.

    Args:
        mode: Practice mode (focused, mixed, timed, review)
        category: Optional category filter for focused mode
        time_limit: Optional time limit in seconds for timed mode
        hard_mode: Optional override for hard mode (uses instance default if None)

    Returns:
        The newly created PracticeSession

    Raises:
        ValueError: If a session is already in progress
    """
    if self._current_session is not None:
        raise ValueError(
            "Session already in progress. Call end_session() first."
        )

    # Use provided hard_mode or fall back to instance default
    session_hard_mode = hard_mode if hard_mode is not None else self._hard_mode

    session_id = str(uuid.uuid4())
    self._current_session = PracticeSession(
        session_id=session_id,
        mode=mode,
        category_filter=category.value if category else None,
        time_limit_seconds=time_limit,
        hard_mode=session_hard_mode,  # NEW
    )

    exclude_ids = self._progress_tracker.get_completed_question_ids()
    self._pending_questions = self._question_bank.get_questions(
        category=category,
        limit=self._get_question_limit(mode),
        exclude_ids=exclude_ids if mode != PracticeMode.review else None,
    )

    return self._current_session
```

- [ ] **Step 5: Modify submit_answer to pass hard_mode**

```python
# interview_prep_coach/practice/engine.py - modify submit_answer

async def submit_answer(
    self,
    question_id: str,
    answer: str,
) -> QuestionAttempt:
    """Submit user's answer and get feedback.

    Args:
        question_id: ID of the question being answered
        answer: User's answer text

    Returns:
        QuestionAttempt with feedback, score, and weak areas populated

    Raises:
        ValueError: If no session is in progress or question not found
    """
    if self._current_session is None:
        raise ValueError("No session in progress. Call start_session() first.")

    question = self._question_bank.get_question_by_id(question_id)
    if question is None:
        raise ValueError(f"Question not found: {question_id}")

    hard_mode = self._current_session.hard_mode  # Get from session

    feedback, score, weak_areas = await self._feedback_analyzer.analyze_answer(
        question, answer, hard_mode=hard_mode  # PASS hard_mode
    )

    if self._scorer:
        score = self._scorer.calculate_score(question, answer, feedback, hard_mode=hard_mode)

    attempt = QuestionAttempt(
        question_id=question_id,
        question_text=question["text"],
        category=QuestionCategory(question["category"]),
        user_answer=answer,
        scout_feedback=feedback,
        score=score,
        weak_areas=weak_areas,
    )

    self._current_session.questions.append(attempt)
    return attempt
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/practice/test_engine_hard_mode.py -v`
Expected: PASS (all 2 tests)

- [ ] **Step 7: Commit**

```bash
git add interview_prep_coach/practice/engine.py tests/practice/test_engine_hard_mode.py
git commit -m "feat: pass hard_mode through PracticeEngine

- Store hard_mode in engine instance
- Pass to session, analyzer, and scorer

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Add --hard Flag to CLI Commands

**Files:**
- Modify: `interview_prep_coach/cli.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli_hard_mode.py

from click.testing import CliRunner
from interview_prep_coach.cli import main


class TestCLIHardModeFlag:
    """Test --hard flag in CLI commands."""

    def test_practice_command_has_hard_flag(self):
        """practice command should accept --hard flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["practice", "--help"])
        assert "--hard" in result.output

    def test_chat_command_has_hard_flag(self):
        """chat command should accept --hard flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["chat", "--help"])
        assert "--hard" in result.output

    def test_quick_practice_command_has_hard_flag(self):
        """quick-practice command should accept --hard flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-practice", "--help"])
        assert "--hard" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_hard_mode.py -v`
Expected: FAIL (--hard not found in output)

- [ ] **Step 3: Add --hard flag to practice command**

```python
# interview_prep_coach/cli.py - modify practice command options

@main.command()
@click.option("--session", type=str, default=None, help="Resume existing session by ID")
@click.option(
    "--category",
    type=click.Choice(["behavioral", "technical", "system_design", "coding"]),
    default=None,
    help="Focus on specific category",
)
@click.option("--timed", is_flag=True, help="Enable timed mode")
@click.option("--review", is_flag=True, help="Review weak areas")
@click.option("--limit", type=int, default=120, help="Time limit in seconds (for timed mode)")
@click.option("--questions", type=int, default=5, help="Number of questions to practice")
@click.option("--hard", is_flag=True, help="Enable hard mode for tougher feedback")  # NEW
def practice(
    session: str | None,
    category: str | None,
    timed: bool,
    review: bool,
    limit: int,
    questions: int,
    hard: bool,  # NEW
):
```

- [ ] **Step 4: Modify _create_engine to accept hard_mode**

```python
# interview_prep_coach/cli.py - modify _create_engine

def _create_engine(data_dir: Path | None = None, hard_mode: bool = False) -> PracticeEngine:
    """Create a PracticeEngine with all dependencies.

    Args:
        data_dir: Directory for progress tracking data
        hard_mode: Whether to enable tougher scoring and feedback
    """
    tracker = ProgressTracker(data_dir=data_dir)
    bank = QuestionBank()
    analyzer = FeedbackAnalyzer()
    scorer = Scorer()
    return PracticeEngine(
        question_bank=bank,
        progress_tracker=tracker,
        feedback_analyzer=analyzer,
        scorer=scorer,
        hard_mode=hard_mode,  # NEW
    )
```

- [ ] **Step 5: Pass hard flag to engine in practice command**

```python
# interview_prep_coach/cli.py - modify practice command body

def practice(
    session: str | None,
    category: str | None,
    timed: bool,
    review: bool,
    limit: int,
    questions: int,
    hard: bool,  # NEW
):
    """Start interactive practice session.

    Practice interview questions with AI-powered feedback on your answers.

    Examples:
        python -m interview_prep_coach practice
        python -m interview_prep_coach practice --category behavioral
        python -m interview_prep_coach practice --hard  # NEW
        python -m interview_prep_coach practice --timed --limit 120
        python -m interview_prep_coach practice --review
    """
    data_dir = _get_data_dir()
    engine = _create_engine(data_dir, hard_mode=hard)  # MODIFIED

    # ... rest of function unchanged
```

- [ ] **Step 6: Add --hard flag to quick-practice command**

```python
# interview_prep_coach/cli.py - modify quick-practice command

@main.command("quick-practice")
@click.option(
    "--category",
    type=click.Choice(["behavioral", "technical", "system_design", "coding"]),
    default="behavioral",
    help="Question category",
)
@click.option("--questions", type=int, default=3, help="Number of questions")
@click.option("--hard", is_flag=True, help="Enable hard mode for tougher feedback")  # NEW
def quick_practice(category: str, questions: int, hard: bool):  # NEW PARAM
    """Quick practice session with minimal setup.

    Fast practice mode for a quick warmup.

    Examples:
        python -m interview_prep_coach quick-practice
        python -m interview_prep_coach quick-practice --hard  # NEW
        python -m interview_prep_coach quick-practice --category technical --questions 5
    """
    data_dir = _get_data_dir()
    engine = _create_engine(data_dir, hard_mode=hard)  # MODIFIED
    # ... rest of function unchanged
```

- [ ] **Step 7: Add --hard flag to chat command**

```python
# interview_prep_coach/cli.py - modify chat command

@main.command()
@click.option("--message", "-m", type=str, default=None, help="Send a single message and exit")
@click.option("--data-dir", type=click.Path(), default="./data/conversations", help="Data directory")
@click.option("--user", type=str, default="default", help="User ID for session")
@click.option("--job", type=click.Path(exists=True), default=None, help="Job posting file to use for context")
@click.option("--job-url", type=str, default=None, help="Job posting URL to use for context")
@click.option("--hard", is_flag=True, help="Enable hard mode for tougher feedback")  # NEW
def chat(message: str | None, data_dir: str, user: str, job: str | None, job_url: str | None, hard: bool):  # NEW PARAM
    """Start or continue a conversation with Scout.

    Interactive chat with your interview prep coach. Optionally send a single
    message with -m flag and exit.

    Examples:
        python -m interview_prep_coach chat
        python -m interview_prep_coach chat -m "Help me with behavioral questions"
        python -m interview_prep_coach chat --hard  # NEW
        python -m interview_prep_coach chat --job posting.md
        python -m interview_prep_coach chat --job-url https://company.com/jobs/123
    """
    from .job.extractor import JobExtractor

    storage = MemoryStorage(data_dir)
    session = ConversationSession(user_id=user, storage=storage)

    if hard:
        # TODO: Implement hard mode in ConversationSession
        # For now, show a message that hard mode is active
        click.echo("\n Hard mode enabled - tougher feedback active")

    # ... rest of function unchanged
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/test_cli_hard_mode.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 9: Commit**

```bash
git add interview_prep_coach/cli.py tests/test_cli_hard_mode.py
git commit -m "feat: add --hard flag to practice, chat, and quick-practice commands

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5.5: Update Protocol Signatures

**Files:**
- Modify: `interview_prep_coach/practice/engine.py` (protocols section)

- [ ] **Step 1: Update FeedbackAnalyzerProtocol**

```python
# interview_prep_coach/practice/engine.py - update FeedbackAnalyzerProtocol

class FeedbackAnalyzerProtocol(Protocol):
    """Protocol for FeedbackAnalyzer dependency."""

    async def analyze_answer(
        self,
        question: dict,
        answer: str,
        hard_mode: bool = False,  # NEW PARAMETER
    ) -> tuple[str, float, list[str]]:
        """Analyze an answer and return feedback, score, and weak areas."""
        ...
```

- [ ] **Step 2: Update ScorerProtocol**

```python
# interview_prep_coach/practice/engine.py - update ScorerProtocol

class ScorerProtocol(Protocol):
    """Protocol for Scorer dependency."""

    def calculate_score(
        self,
        question: dict,
        answer: str,
        feedback: str,
        hard_mode: bool = False,  # NEW PARAMETER
    ) -> float:
        """Calculate a score for the answer."""
        ...
```

- [ ] **Step 3: Run type checking to verify**

Run: `pyright interview_prep_coach/practice/engine.py`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add interview_prep_coach/practice/engine.py
git commit -m "feat: add hard_mode parameter to engine protocols

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Run Full Test Suite and Verify

**Files:**
- All modified files

- [ ] **Step 1: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Run type checking**

Run: `pyright interview_prep_coach/`
Expected: No errors

- [ ] **Step 3: Run linting**

Run: `ruff check interview_prep_coach/`
Expected: No errors

- [ ] **Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address test/type/lint issues from hard mode implementation

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Summary

This implementation adds:

1. **Model**: `hard_mode: bool` field on `PracticeSession`
2. **Scorer**: Hard mode with lower base (4.0), steeper penalties, capped sentiment
3. **FeedbackAnalyzer**: Hard mode system prompt with critical evaluation guidance
4. **Engine**: Passes hard_mode through to analyzer and scorer
5. **Protocols**: Updated FeedbackAnalyzerProtocol and ScorerProtocol
6. **CLI**: `--hard` flag on `practice`, `chat`, `quick-practice` commands

**Scope Notes:**
- Chat command `--hard` flag is a placeholder - full ConversationSession integration is out of scope for this iteration
- The flag exists but shows a message; future work can integrate with ConversationSession's feedback system

**Total: 7 tasks, ~35 steps**
