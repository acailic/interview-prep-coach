# Answer Versioning & Job Context Design

**Date:** 2026-02-24
**Status:** Approved
**Goal:** Enable answer refinement tracking and job-specific personalization

## Overview

Two features that work together:
1. **Answer Versioning** - Track answer iterations, compare versions, mark best
2. **Job Context** - Load job posting, extract requirements, tailor feedback

## Component 1: Answer Versioning

### Approach: Best + Current

Keep the "best" version and current work-in-progress, not every iteration.

### Data Models

```python
class AnswerVersion(BaseModel):
    """A single version of an answer to a practice question."""
    version_number: int
    content: str
    created_at: datetime
    feedback: str  # Scout's feedback on this version
    scores: dict[str, float]  # {"clarity": 7.5, "completeness": 6.0}

class AnswerHistory(BaseModel):
    """Tracks versions of an answer to a question."""
    question_id: str
    question_text: str
    versions: list[AnswerVersion]
    best_version_id: int | None  # Which version user marked as best
    current_version_id: int
```

### Storage

Persisted in `data/answers/<question_id>.json`

### User Flow

1. User answers question → stored as version 1
2. User says "let me try again" → Scout recognizes refinement intent
3. New answer stored as version 2
4. Scout compares: "Version 2 is clearer, but version 1 had stronger impact"
5. User can say "mark this as best" → Scout remembers

### Refinement Intent Detection

Triggers when user says:
- "let me try again"
- "another attempt"
- "let me refine that"
- "one more time"

### Best Version Commands

- "mark this as best" - marks current version as best
- "show me my best answer" - recalls best version
- "compare versions" - side-by-side comparison

## Component 2: Job Context

### CLI Usage

```bash
# Start with job file
interview-prep chat --job path/to/posting.md

# Start with job URL
interview-prep chat --job-url https://company.com/jobs/123
```

### Data Model

```python
class JobContext(BaseModel):
    """Extracted job posting information."""
    company: str
    position: str
    requirements: list[str]
    tech_stack: list[str]
    key_skills: list[str]
    raw_posting: str  # Original text for reference
```

### Session Start Flow

1. Scout reads job posting (file or URL)
2. Uses Claude Haiku to extract key information
3. Stores in `WorkingMemory.job_context`
4. Greets with job-aware message

**Example greeting:**
"Hey! Ready to prep for the Senior Engineer role at TechCorp? I see they're big on distributed systems - want to focus there?"

### During Conversation

- Scout references job requirements in feedback
- Questions can be tailored to job requirements
- Comparisons are job-relevant

## Integration: Job-Aware Versioning

When practicing for a specific job, Scout's feedback and comparisons are contextualized:

**Example:**

```
Job: Senior Engineer at TechCorp (Kubernetes, distributed systems)

User answers: "Tell me about a technical challenge"

Version 1 feedback:
  "Good STAR structure. But this role wants distributed systems experience.
   Can you connect the database optimization to multi-region considerations?"

Version 2 feedback:
  "Better! You mentioned replication now. Compare to version 1:
   - V2 added distributed systems angle (+2 relevance)
   - V1 had clearer metrics (-1 specificity)
   Want to add the metrics back in?"
```

## Technical Architecture

### New Files

```
interview_prep_coach/
├── versioning/
│   ├── __init__.py
│   ├── models.py          # AnswerVersion, AnswerHistory
│   ├── tracker.py         # Version management logic
│   └── storage.py         # Persist answers to disk
│
├── job/
│   ├── __init__.py
│   ├── extractor.py       # AI extraction from job posting
│   └── context.py         # JobContext model
```

### Files to Modify

| File | Changes |
|------|---------|
| `cli.py` | Add `--job` and `--job-url` flags to `chat` command |
| `conversation/memory.py` | Add `job_context` field to WorkingMemory |
| `conversation/session.py` | Detect refinement intent, integrate versioning |

## Memory Integration

```python
# Extend existing WorkingMemory
class WorkingMemory(BaseModel):
    current_context: InterviewContext | None  # Already exists
    job_context: JobContext | None  # NEW: Full job posting analysis
    # ... existing fields ...
```

## Session Flow

```
interview-prep chat --job posting.md
    ↓
Scout extracts job info → stores in WorkingMemory
    ↓
Scout greets with job-aware message
    ↓
User practices → Scout gives job-relevant feedback
    ↓
User refines answer → Scout tracks versions + compares
    ↓
User marks "best" → Scout remembers for future
```

## Success Criteria

- User can provide job posting via file or URL
- Scout greets with job-specific context
- User can refine answers multiple times
- Scout compares versions with meaningful feedback
- User can mark and recall "best" version
- Job context influences all feedback and suggestions
