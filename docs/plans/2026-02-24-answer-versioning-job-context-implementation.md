# Answer Versioning & Job Context Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Enable answer refinement tracking and job-specific personalization in Scout

**Architecture:** Two new modules (`versioning/` and `job/`) integrated into the existing conversation session. Versioning tracks best+current versions per question. Job context extracts requirements from postings and influences feedback.

**Tech Stack:** Pydantic models, Claude Haiku for job extraction, existing conversation infrastructure.

---

## Task 1: Answer Versioning Models

**Files:**
- Create: `interview_prep_coach/versioning/__init__.py`
- Create: `interview_prep_coach/versioning/models.py`
- Create: `tests/versioning/__init__.py`
- Create: `tests/versioning/test_models.py`

**Step 1: Write the failing test**

```python
# tests/versioning/test_models.py
"""Tests for answer versioning models."""

from datetime import datetime
from interview_prep_coach.versioning.models import AnswerVersion, AnswerHistory


class TestAnswerVersion:
    """Tests for AnswerVersion model."""

    def test_create_version(self):
        """Should create an answer version with required fields."""
        version = AnswerVersion(
            version_number=1,
            content="I led a project that improved performance by 40%",
            created_at=datetime.now(),
            feedback="Good use of metrics",
            scores={"clarity": 7.5, "completeness": 6.0},
        )
        assert version.version_number == 1
        assert "40%" in version.content
        assert version.scores["clarity"] == 7.5

    def test_default_scores(self):
        """Should allow empty scores dict."""
        version = AnswerVersion(
            version_number=1,
            content="Test answer",
            created_at=datetime.now(),
            feedback="Test feedback",
        )
        assert version.scores == {}


class TestAnswerHistory:
    """Tests for AnswerHistory model."""

    def test_create_empty_history(self):
        """Should create history with no versions."""
        history = AnswerHistory(
            question_id="q1",
            question_text="Tell me about yourself",
        )
        assert history.question_id == "q1"
        assert history.versions == []
        assert history.best_version_id is None
        assert history.current_version_id == 0

    def test_add_version(self):
        """Should add a version to history."""
        history = AnswerHistory(
            question_id="q1",
            question_text="Tell me about yourself",
        )
        version = AnswerVersion(
            version_number=1,
            content="Test answer",
            created_at=datetime.now(),
            feedback="Good start",
        )
        history.add_version(version)
        assert len(history.versions) == 1
        assert history.current_version_id == 1

    def test_mark_best(self):
        """Should mark a version as best."""
        history = AnswerHistory(
            question_id="q1",
            question_text="Tell me about yourself",
        )
        version = AnswerVersion(
            version_number=1,
            content="Test answer",
            created_at=datetime.now(),
            feedback="Good start",
        )
        history.add_version(version)
        history.mark_best(1)
        assert history.best_version_id == 1

    def test_get_version(self):
        """Should retrieve a specific version."""
        history = AnswerHistory(
            question_id="q1",
            question_text="Tell me about yourself",
        )
        v1 = AnswerVersion(
            version_number=1,
            content="First attempt",
            created_at=datetime.now(),
            feedback="Okay",
        )
        v2 = AnswerVersion(
            version_number=2,
            content="Second attempt",
            created_at=datetime.now(),
            feedback="Better",
        )
        history.add_version(v1)
        history.add_version(v2)

        retrieved = history.get_version(2)
        assert retrieved.content == "Second attempt"
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/versioning/test_models.py -v`
Expected: FAIL with module import errors

**Step 3: Write implementation**

```python
# interview_prep_coach/versioning/__init__.py
"""Answer versioning for tracking iterations."""

from .models import AnswerVersion, AnswerHistory

__all__ = ["AnswerVersion", "AnswerHistory"]
```

```python
# interview_prep_coach/versioning/models.py
"""Models for answer versioning."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AnswerVersion(BaseModel):
    """A single version of an answer to a practice question."""

    version_number: int
    content: str
    created_at: datetime
    feedback: str
    scores: dict[str, float] = Field(default_factory=dict)


class AnswerHistory(BaseModel):
    """Tracks versions of an answer to a question."""

    question_id: str
    question_text: str
    versions: list[AnswerVersion] = Field(default_factory=list)
    best_version_id: Optional[int] = None
    current_version_id: int = 0

    def add_version(self, version: AnswerVersion) -> None:
        """Add a new version to history."""
        self.versions.append(version)
        self.current_version_id = version.version_number

    def mark_best(self, version_number: int) -> None:
        """Mark a version as the best one."""
        if any(v.version_number == version_number for v in self.versions):
            self.best_version_id = version_number

    def get_version(self, version_number: int) -> Optional[AnswerVersion]:
        """Retrieve a specific version by number."""
        for version in self.versions:
            if version.version_number == version_number:
                return version
        return None

    def get_best_version(self) -> Optional[AnswerVersion]:
        """Retrieve the best marked version."""
        if self.best_version_id is None:
            return None
        return self.get_version(self.best_version_id)

    def get_current_version(self) -> Optional[AnswerVersion]:
        """Retrieve the current (latest) version."""
        if not self.versions:
            return None
        return self.get_version(self.current_version_id)

    def get_next_version_number(self) -> int:
        """Get the version number for the next version."""
        if not self.versions:
            return 1
        return max(v.version_number for v in self.versions) + 1
```

**Step 4: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/versioning/test_models.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/versioning/ tests/versioning/ && git commit -m "feat: add AnswerVersion and AnswerHistory models

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Answer Version Storage

**Files:**
- Create: `interview_prep_coach/versioning/storage.py`
- Create: `tests/versioning/test_storage.py`

**Step 1: Write the failing test**

```python
# tests/versioning/test_storage.py
"""Tests for answer version storage."""

import pytest
from pathlib import Path
from datetime import datetime
from interview_prep_coach.versioning.storage import AnswerStorage
from interview_prep_coach.versioning.models import AnswerVersion, AnswerHistory


class TestAnswerStorage:
    """Tests for answer storage."""

    @pytest.fixture
    def storage(self, tmp_path):
        return AnswerStorage(data_dir=tmp_path)

    def test_save_and_load_history(self, storage):
        """Should persist and retrieve answer history."""
        history = AnswerHistory(
            question_id="q1",
            question_text="Tell me about yourself",
        )
        version = AnswerVersion(
            version_number=1,
            content="Test answer",
            created_at=datetime.now(),
            feedback="Good start",
        )
        history.add_version(version)

        storage.save(history)
        loaded = storage.load("q1")

        assert loaded is not None
        assert loaded.question_id == "q1"
        assert len(loaded.versions) == 1
        assert loaded.versions[0].content == "Test answer"

    def test_load_nonexistent_returns_none(self, storage):
        """Should return None for nonexistent history."""
        result = storage.load("nonexistent")
        assert result is None

    def test_list_question_ids(self, storage):
        """Should list all stored question IDs."""
        history1 = AnswerHistory(question_id="q1", question_text="Q1")
        history2 = AnswerHistory(question_id="q2", question_text="Q2")

        storage.save(history1)
        storage.save(history2)

        ids = storage.list_question_ids()
        assert "q1" in ids
        assert "q2" in ids
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/versioning/test_storage.py -v`
Expected: FAIL with module import errors

**Step 3: Write implementation**

```python
# interview_prep_coach/versioning/storage.py
"""Storage for answer versioning."""

from pathlib import Path
from typing import Optional
from .models import AnswerHistory


class AnswerStorage:
    """Persists answer histories to disk."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir) / "answers"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save(self, history: AnswerHistory) -> None:
        """Save answer history to disk."""
        path = self.data_dir / f"{history.question_id}.json"
        path.write_text(history.model_dump_json(indent=2))

    def load(self, question_id: str) -> Optional[AnswerHistory]:
        """Load answer history from disk."""
        path = self.data_dir / f"{question_id}.json"
        if not path.exists():
            return None
        return AnswerHistory.model_validate_json(path.read_text())

    def list_question_ids(self) -> list[str]:
        """List all stored question IDs."""
        return [p.stem for p in self.data_dir.glob("*.json")]

    def delete(self, question_id: str) -> None:
        """Delete answer history."""
        path = self.data_dir / f"{question_id}.json"
        if path.exists():
            path.unlink()
```

**Step 4: Update __init__.py**

```python
# interview_prep_coach/versioning/__init__.py
"""Answer versioning for tracking iterations."""

from .models import AnswerVersion, AnswerHistory
from .storage import AnswerStorage

__all__ = ["AnswerVersion", "AnswerHistory", "AnswerStorage"]
```

**Step 5: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/versioning/test_storage.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/versioning/ tests/versioning/test_storage.py && git commit -m "feat: add AnswerStorage for persisting answer histories

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Job Context Models

**Files:**
- Create: `interview_prep_coach/job/__init__.py`
- Create: `interview_prep_coach/job/context.py`
- Create: `tests/job/__init__.py`
- Create: `tests/job/test_context.py`

**Step 1: Write the failing test**

```python
# tests/job/test_context.py
"""Tests for job context models."""

from interview_prep_coach.job.context import JobContext


class TestJobContext:
    """Tests for JobContext model."""

    def test_create_job_context(self):
        """Should create job context with all fields."""
        context = JobContext(
            company="TechCorp",
            position="Senior Engineer",
            requirements=["5+ years experience", "Distributed systems"],
            tech_stack=["Python", "Kubernetes", "PostgreSQL"],
            key_skills=["System design", "Team leadership"],
            raw_posting="Original job posting text...",
        )
        assert context.company == "TechCorp"
        assert context.position == "Senior Engineer"
        assert "Python" in context.tech_stack
        assert len(context.requirements) == 2

    def test_minimal_job_context(self):
        """Should create with minimal fields."""
        context = JobContext(
            company="StartupXYZ",
            position="Engineer",
            raw_posting="Job posting",
        )
        assert context.company == "StartupXYZ"
        assert context.requirements == []
        assert context.tech_stack == []
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/job/test_context.py -v`
Expected: FAIL with module import errors

**Step 3: Write implementation**

```python
# interview_prep_coach/job/__init__.py
"""Job context for personalized coaching."""

from .context import JobContext

__all__ = ["JobContext"]
```

```python
# interview_prep_coach/job/context.py
"""Job context model."""

from pydantic import BaseModel, Field


class JobContext(BaseModel):
    """Extracted job posting information."""

    company: str
    position: str
    requirements: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    key_skills: list[str] = Field(default_factory=list)
    raw_posting: str = ""

    def to_context_string(self) -> str:
        """Format job context for inclusion in prompts."""
        parts = [f"Company: {self.company}", f"Position: {self.position}"]

        if self.requirements:
            parts.append(f"Requirements: {', '.join(self.requirements)}")
        if self.tech_stack:
            parts.append(f"Tech Stack: {', '.join(self.tech_stack)}")
        if self.key_skills:
            parts.append(f"Key Skills: {', '.join(self.key_skills)}")

        return "\n".join(parts)

    def get_summary(self) -> str:
        """Get a brief summary for greetings."""
        return f"{self.position} at {self.company}"
```

**Step 4: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/job/test_context.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/job/ tests/job/ && git commit -m "feat: add JobContext model for job posting data

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Job Posting Extractor

**Files:**
- Create: `interview_prep_coach/job/extractor.py`
- Modify: `interview_prep_coach/job/__init__.py`
- Create: `tests/job/test_extractor.py`

**Step 1: Write the failing test**

```python
# tests/job/test_extractor.py
"""Tests for job posting extraction."""

import pytest
from unittest.mock import Mock
from interview_prep_coach.job.extractor import JobExtractor
from interview_prep_coach.job.context import JobContext


class TestJobExtractor:
    """Tests for job posting extraction."""

    def test_extract_from_text(self, monkeypatch):
        """Should extract job context from posting text."""
        mock_response = Mock()
        mock_response.content = [Mock(text='''{
            "company": "TechCorp",
            "position": "Senior Engineer",
            "requirements": ["5+ years Python", "Distributed systems experience"],
            "tech_stack": ["Python", "Kubernetes", "PostgreSQL"],
            "key_skills": ["System design", "Mentorship"]
        }''')]

        extractor = JobExtractor(api_key="test-key")
        monkeypatch.setattr(
            extractor.client.messages,
            "create",
            Mock(return_value=mock_response)
        )

        result = extractor.extract("TechCorp is hiring a Senior Engineer...")
        assert isinstance(result, JobContext)
        assert result.company == "TechCorp"
        assert result.position == "Senior Engineer"
        assert "Python" in result.tech_stack

    def test_extract_handles_malformed_response(self, monkeypatch):
        """Should handle malformed AI response gracefully."""
        mock_response = Mock()
        mock_response.content = [Mock(text="not valid json")]

        extractor = JobExtractor(api_key="test-key")
        monkeypatch.setattr(
            extractor.client.messages,
            "create",
            Mock(return_value=mock_response)
        )

        result = extractor.extract("Some job posting")
        assert result.company == "Unknown Company"
        assert result.position == "Unknown Position"
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/job/test_extractor.py -v`
Expected: FAIL with module import errors

**Step 3: Write implementation**

```python
# interview_prep_coach/job/extractor.py
"""Extract job context from postings using AI."""

import json
from typing import Optional
from anthropic import Anthropic
from pydantic import BaseModel

from .context import JobContext
from interview_prep_coach.utils.logger import get_logger

logger = get_logger(__name__)

EXTRACTION_PROMPT = """Extract job posting information from this text.

Job Posting:
{posting}

Return JSON with these fields:
- company: Company name
- position: Job title
- requirements: List of key requirements
- tech_stack: List of technologies mentioned
- key_skills: List of important skills

Return only valid JSON, no other text."""


class JobExtractor:
    """Extract job context from postings using Claude Haiku."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()

    def extract(self, posting_text: str) -> JobContext:
        """Extract job context from posting text."""
        prompt = EXTRACTION_PROMPT.format(posting=posting_text)

        try:
            response = self.client.messages.create(
                model="claude-haiku-3-5-20241022",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )

            data = json.loads(response.content[0].text)
            return JobContext(
                company=data.get("company", "Unknown Company"),
                position=data.get("position", "Unknown Position"),
                requirements=data.get("requirements", []),
                tech_stack=data.get("tech_stack", []),
                key_skills=data.get("key_skills", []),
                raw_posting=posting_text,
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse job extraction response: {e}")
            return JobContext(
                company="Unknown Company",
                position="Unknown Position",
                raw_posting=posting_text,
            )
        except Exception as e:
            logger.error(f"Job extraction failed: {e}")
            return JobContext(
                company="Unknown Company",
                position="Unknown Position",
                raw_posting=posting_text,
            )

    def extract_from_file(self, file_path: str) -> JobContext:
        """Extract job context from a file."""
        with open(file_path, "r") as f:
            return self.extract(f.read())

    def extract_from_url(self, url: str) -> JobContext:
        """Extract job context from a URL (fetches content)."""
        import httpx
        from bs4 import BeautifulSoup

        response = httpx.get(url, follow_redirects=True)
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract text from the page
        text = soup.get_text(separator="\n", strip=True)
        return self.extract(text)
```

**Step 4: Update __init__.py**

```python
# interview_prep_coach/job/__init__.py
"""Job context for personalized coaching."""

from .context import JobContext
from .extractor import JobExtractor

__all__ = ["JobContext", "JobExtractor"]
```

**Step 5: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/job/test_extractor.py -v`
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/job/ tests/job/test_extractor.py && git commit -m "feat: add JobExtractor for parsing job postings with AI

Uses Claude Haiku to extract company, position, requirements, tech stack, and key skills.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Update WorkingMemory with Job Context

**Files:**
- Modify: `interview_prep_coach/conversation/memory.py`
- Modify: `tests/conversation/test_memory.py`

**Step 1: Write the failing test**

```python
# Add to tests/conversation/test_memory.py

from interview_prep_coach.job.context import JobContext


class TestWorkingMemoryJobContext:
    """Tests for job context in working memory."""

    def test_set_job_context(self):
        """Should set job context in working memory."""
        memory = WorkingMemory()
        job = JobContext(
            company="TechCorp",
            position="Senior Engineer",
            tech_stack=["Python", "Kubernetes"],
        )
        memory.set_job_context(job)

        assert memory.job_context is not None
        assert memory.job_context.company == "TechCorp"

    def test_to_context_string_includes_job(self):
        """Should include job context in context string."""
        memory = WorkingMemory()
        job = JobContext(
            company="TechCorp",
            position="Senior Engineer",
            tech_stack=["Python"],
        )
        memory.set_job_context(job)

        context = memory.to_context_string()
        assert "TechCorp" in context
        assert "Senior Engineer" in context
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_memory.py::TestWorkingMemoryJobContext -v`
Expected: FAIL

**Step 3: Modify memory.py**

```python
# Add to imports in conversation/memory.py
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from interview_prep_coach.job.context import JobContext

# Add field to WorkingMemory class:
class WorkingMemory(BaseModel):
    current_context: Optional[InterviewContext] = None
    recent_weaknesses: list[str] = Field(default_factory=list)
    recent_strengths: list[str] = Field(default_factory=list)
    style_preferences: dict[str, str] = Field(default_factory=dict)
    last_session_summary: Optional[str] = None
    job_context: Optional["JobContext"] = None  # NEW

    def set_job_context(self, job: "JobContext") -> None:
        """Set the job context for personalized coaching."""
        self.job_context = job

    # Update to_context_string to include job context:
    def to_context_string(self) -> str:
        parts = []

        # Job context first (most relevant for personalization)
        if self.job_context:
            parts.append(f"Target Role: {self.job_context.get_summary()}")
            if self.job_context.tech_stack:
                parts.append(f"Tech Stack: {', '.join(self.job_context.tech_stack)}")
            if self.job_context.key_skills:
                parts.append(f"Key Skills: {', '.join(self.job_context.key_skills)}")

        if self.current_context:
            ctx = self.current_context
            parts.append(f"Company: {ctx.company}")
            if ctx.position:
                parts.append(f"Position: {ctx.position}")
            if ctx.days_until_interview is not None:
                parts.append(f"Days until interview: {ctx.days_until_interview}")

        if self.recent_weaknesses:
            parts.append(f"Areas to improve: {', '.join(self.recent_weaknesses)}")

        if self.recent_strengths:
            parts.append(f"Strengths shown: {', '.join(self.recent_strengths)}")

        if self.style_preferences:
            prefs = [f"{k}: {v}" for k, v in self.style_preferences.items()]
            parts.append(f"Style preferences: {', '.join(prefs)}")

        if self.last_session_summary:
            parts.append(f"Last session: {self.last_session_summary}")

        return "\n".join(parts)
```

**Step 4: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_memory.py -v`
Expected: All tests pass

**Step 5: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/conversation/memory.py tests/conversation/test_memory.py && git commit -m "feat: add job_context to WorkingMemory

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Update CLI with Job Flags

**Files:**
- Modify: `interview_prep_coach/cli.py`
- Create: `tests/test_cli_job_flags.py`

**Step 1: Write the failing test**

```python
# tests/test_cli_job_flags.py
"""Tests for job-related CLI flags."""

from click.testing import CliRunner
from interview_prep_coach.cli import main


class TestChatJobFlags:
    """Tests for --job and --job-url flags."""

    def test_chat_help_shows_job_flags(self):
        """Help should show --job and --job-url options."""
        runner = CliRunner()
        result = runner.invoke(main, ["chat", "--help"])
        assert "--job" in result.output
        assert "--job-url" in result.output
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/test_cli_job_flags.py -v`
Expected: FAIL

**Step 3: Modify cli.py**

Add new options to the `chat` command:

```python
@main.command()
@click.option("--message", "-m", type=str, default=None, help="Send a single message and exit")
@click.option("--data-dir", type=click.Path(), default="./data/conversations", help="Data directory")
@click.option("--user", type=str, default="default", help="User ID for session")
@click.option("--job", type=click.Path(exists=True), default=None, help="Job posting file to use for context")
@click.option("--job-url", type=str, default=None, help="Job posting URL to use for context")
def chat(message: str | None, data_dir: str, user: str, job: str | None, job_url: str | None):
    """Start or continue a conversation with Scout.

    Interactive chat with your interview prep coach. Optionally send a single
    message with -m flag and exit.

    Examples:
        python -m interview_prep_coach chat
        python -m interview_prep_coach chat -m "Help me with behavioral questions"
        python -m interview_prep_coach chat --job posting.md
        python -m interview_prep_coach chat --job-url https://company.com/jobs/123
    """
    from .job.extractor import JobExtractor

    storage = MemoryStorage(data_dir)
    session = ConversationSession(user_id=user, storage=storage)

    # Load job context if provided
    if job or job_url:
        extractor = JobExtractor()
        if job:
            job_context = extractor.extract_from_file(job)
        else:
            job_context = extractor.extract_from_url(job_url)
        session.set_job_context(job_context)
        click.echo(f"\n Job loaded: {job_context.get_summary()}")

    if message:
        response = session.send_message(message)
        click.echo(response)
        return

    click.echo("\n Scout - Your Interview Prep Coach")
    click.echo(" Type 'quit' to exit, 'style <feedback>' to adjust coaching style\n")

    # ... rest of existing chat implementation
```

**Step 4: Update ConversationSession to accept job context**

Add to `conversation/session.py`:

```python
def set_job_context(self, job: JobContext) -> None:
    """Set job context for personalized coaching."""
    self.working_memory.set_job_context(job)
    self._save_state()
```

**Step 5: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/test_cli_job_flags.py -v`
Expected: PASS

**Step 6: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/cli.py interview_prep_coach/conversation/session.py tests/test_cli_job_flags.py && git commit -m "feat: add --job and --job-url flags to chat command

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Integrate Answer Versioning into Session

**Files:**
- Modify: `interview_prep_coach/conversation/session.py`
- Create: `tests/conversation/test_session_versioning.py`

**Step 1: Write the failing test**

```python
# tests/conversation/test_session_versioning.py
"""Tests for answer versioning in session."""

import pytest
from unittest.mock import Mock
from interview_prep_coach.conversation.session import ConversationSession
from interview_prep_coach.conversation.storage import MemoryStorage


class TestSessionVersioning:
    """Tests for answer versioning integration."""

    @pytest.fixture
    def storage(self, tmp_path):
        return MemoryStorage(str(tmp_path))

    def test_detect_refinement_intent(self, storage):
        """Should detect when user wants to refine an answer."""
        session = ConversationSession(user_id="test", storage=storage)
        assert session._is_refinement_intent("let me try again")
        assert session._is_refinement_intent("another attempt")
        assert session._is_refinement_intent("let me refine that")
        assert not session._is_refinement_intent("new question")

    def test_detect_mark_best_intent(self, storage):
        """Should detect when user wants to mark best version."""
        session = ConversationSession(user_id="test", storage=storage)
        assert session._is_mark_best_intent("mark this as best")
        assert session._is_mark_best_intent("that's my best answer")
        assert not session._is_mark_best_intent("good answer")
```

**Step 2: Run test to verify it fails**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_session_versioning.py -v`
Expected: FAIL

**Step 3: Add versioning methods to session.py**

```python
# Add imports to session.py
from ..versioning.storage import AnswerStorage
from ..versioning.models import AnswerVersion, AnswerHistory
from interview_prep_coach.utils.logger import get_logger

logger = get_logger(__name__)

# Add to __init__:
self.answer_storage = AnswerStorage(data_dir=storage.data_dir)
self._current_question_id: str | None = None

# Add intent detection methods:
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
```

**Step 4: Run test to verify it passes**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/conversation/test_session_versioning.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add interview_prep_coach/conversation/session.py tests/conversation/test_session_versioning.py && git commit -m "feat: add intent detection for answer versioning

Detects refinement, mark-best, show-best, and compare intents.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 8: Full Test Suite

**Step 1: Run all tests**

Run: `cd /home/nistrator/Documents/github/interview-prep-coach && pytest tests/ -v`
Expected: All tests pass

**Step 2: Fix any failures**

If tests fail, fix before proceeding.

**Step 3: Final commit**

```bash
cd /home/nistrator/Documents/github/interview-prep-coach && git add -A && git commit -m "test: verify all tests passing after answer versioning and job context

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Summary

After completing all tasks:
- Answer versioning tracks best + current versions
- Job context extracted from file or URL
- CLI has `--job` and `--job-url` flags
- Session detects refinement intents
- Job context influences feedback

**Files created:**
- `interview_prep_coach/versioning/__init__.py`
- `interview_prep_coach/versioning/models.py`
- `interview_prep_coach/versioning/storage.py`
- `interview_prep_coach/job/__init__.py`
- `interview_prep_coach/job/context.py`
- `interview_prep_coach/job/extractor.py`
- `tests/versioning/__init__.py`
- `tests/versioning/test_models.py`
- `tests/versioning/test_storage.py`
- `tests/job/__init__.py`
- `tests/job/test_context.py`
- `tests/job/test_extractor.py`
- `tests/test_cli_job_flags.py`
- `tests/conversation/test_session_versioning.py`

**Files modified:**
- `interview_prep_coach/conversation/memory.py`
- `interview_prep_coach/conversation/session.py`
- `interview_prep_coach/cli.py`
- `tests/conversation/test_memory.py`
