# Hard Mode Design

**Date:** 2026-03-18
**Status:** Approved
**Goal:** Add opt-in hard mode for tougher scoring and more critical feedback

## Overview

Users who want to be challenged harder can enable `--hard` mode, which activates stricter scoring thresholds and more critical feedback tone. This is opt-in to preserve the supportive default experience.

## Motivation

Current feedback is designed to be encouraging and supportive. While this helps build confidence, some users want more demanding feedback to push themselves harder and identify weaknesses more aggressively. Hard mode provides this without changing the default experience.

## CLI Usage

```bash
# Practice with hard mode
interview-prep practice --hard

# Chat with hard mode
interview-prep chat --hard

# Quick practice with hard mode
interview-prep quick-practice --hard
```

## Component 1: Tougher Scoring

### Scoring Thresholds

| Aspect | Normal Mode | Hard Mode |
|--------|-------------|-----------|
| Base score | 7.0 | 4.0 |
| 1 weak area penalty | -1.0 | -2.0 |
| 2 weak areas penalty | -2.0 | -4.0 |
| 3+ weak areas penalty | -3.0 to -5.0 | -6.0 (floor at 0) |
| Sentiment adjustment | ±2.0 | ±1.0 |
| Max positive bonus | +2.0 | +1.0 |

### Impact Example

An answer with 2 identified weak areas:

- Normal mode: 7.0 - 2.0 = **5.0** (below average)
- Hard mode: 4.0 - 4.0 = **0.0** (failing)

An answer with 1 weak area and positive sentiment:

- Normal mode: 7.0 - 1.0 + 1.5 = **7.5** (good)
- Hard mode: 4.0 - 2.0 + 0.5 = **2.5** (needs work)

### Implementation

Extend `Scorer` class with hard mode support:

```python
class Scorer:
    def score_answer(
        self,
        feedback: str,
        weak_areas: list[str],
        category: QuestionCategory,
        hard_mode: bool = False,  # NEW
    ) -> float:
        base_score = 4.0 if hard_mode else 7.0
        weak_penalty = self._calculate_weak_area_penalty(weak_areas, hard_mode)
        sentiment_adj = self._analyze_sentiment(feedback, hard_mode)
        ...
```

## Component 2: Critical Feedback Tone

### System Prompt Modification

The feedback analyzer receives a hard mode modifier in its system prompt.

**Normal mode:**
```
Be constructive and specific in feedback. Always provide actionable suggestions.
```

**Hard mode:**
```
Be brutally honest. Identify every weakness without sugar-coating. An 8+ score requires a truly interview-ready, polished answer - the kind that would impress a skeptical interviewer. Default to critique over encouragement. Push the user to be better.
```

### Implementation

Add hard mode prompt variant to `FeedbackAnalyzer`:

```python
class FeedbackAnalyzer:
    HARD_MODE_MODIFIER = """
Be brutally honest in your evaluation. Identify every weakness without sugar-coating.

Score 0-3: Significant gaps, not interview-ready
Score 4-5: Below average, several areas need work
Score 6-7: Acceptable but not impressive
Score 8-9: Polished and impressive
Score 10: Exceptional, would stand out in competitive interviews

Default to critique over encouragement. Push for excellence."""

    def _get_system_prompt(self, category: QuestionCategory, hard_mode: bool = False) -> str:
        base_prompt = self.CATEGORY_PROMPTS.get(category, ...)
        if hard_mode:
            return f"{base_prompt}\n\n{self.HARD_MODE_MODIFIER}"
        return f"{base_prompt}\n\nBe constructive and specific..."
```

## Component 3: CLI Integration

### New Flags

Add `--hard` flag to three commands:

| Command | Flag | Effect |
|---------|------|--------|
| `practice` | `--hard` | Enables hard mode scoring and feedback |
| `chat` | `--hard` | Enables hard mode feedback in conversation |
| `quick-practice` | `--hard` | Enables hard mode for quick sessions |

### CLI Changes

```python
@main.command()
@click.option("--hard", is_flag=True, help="Enable hard mode for tougher feedback")
def practice(hard: bool, ...):
    engine = _create_engine(data_dir, hard_mode=hard)
    ...
```

## Component 4: Session Persistence

### Model Update

```python
class PracticeSession(BaseModel):
    session_id: str
    started_at: datetime
    # ... existing fields ...
    hard_mode: bool = False  # NEW: Track hard mode for session
```

This allows progress tracking to differentiate between normal and hard mode attempts.

## Files to Modify

| File | Changes |
|------|---------|
| `cli.py` | Add `--hard` flag to `practice`, `chat`, `quick-practice` commands |
| `practice/scorer.py` | Add `hard_mode` parameter, implement tougher thresholds |
| `practice/feedback_analyzer.py` | Add hard mode system prompt variant |
| `practice/engine.py` | Pass `hard_mode` through to analyzer and scorer |
| `models.py` | Add `hard_mode: bool` to `PracticeSession` |
| `conversation/session.py` | Support hard mode flag, pass to context builder |

## Example Output Comparison

### Normal Mode

**Question:** Tell me about a time you handled a technical crisis.

**User Answer:** "We had a database outage during Black Friday. I led the team to identify it was a connection pool exhaustion issue. We scaled up the pool and added monitoring."

**Feedback:**
> Good use of the STAR structure. You clearly explained the situation and action. Consider adding more specifics: How many users were affected? What was the recovery time? What monitoring did you add? Score: 7.0/10

### Hard Mode

**Question:** Tell me about a time you handled a technical crisis.

**User Answer:** "We had a database outage during Black Friday. I led the team to identify it was a connection pool exhaustion issue. We scaled up the pool and added monitoring."

**Feedback:**
> This answer lacks impact. "Led the team" is vague - what did YOU actually do? No metrics: how long was the outage? How much revenue was lost? What was the root cause analysis process? "Added monitoring" tells me nothing - what specifically? This would not stand out against candidates who quantify their impact. Score: 4.0/10

## Success Criteria

- `--hard` flag activates tougher scoring in practice sessions
- Feedback tone is noticeably more critical and less encouraging
- Scores in hard mode are 2-3 points lower on average for the same answer
- User can toggle between modes via CLI flag
- Session tracking records which mode was used
- Default behavior (no flag) remains supportive and encouraging
