# Autonomous Evolution Design

**Date:** 2026-02-23
**Status:** Approved
**Goal:** Enable Scout to evolve autonomously through pattern emergence and style drift

## Overview

Scout will learn from conversations without explicit user feedback, developing deeper understanding of the user's needs and evolving a personalized coaching relationship over time.

## Component 1: Pattern Emergence

**AI-extracted insights after each conversation turn**

### PatternExtractor

```python
class ExtractionResult(BaseModel):
    weaknesses: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    engagement_level: str = "medium"  # high | medium | low

class PatternExtractor:
    """Extracts strengths/weaknesses from conversation using AI."""

    def extract(self, user_message: str, assistant_response: str) -> ExtractionResult:
        # Calls Claude (Haiku) with extraction prompt
        # Returns patterns discovered in the exchange
```

### Extraction Prompt

Concise, focused on interview-relevant patterns:
- What topics does user struggle with?
- What answering techniques work well?
- How engaged is the user?

### Integration

After `send_message()` saves the assistant response:
```python
patterns = self.pattern_extractor.extract(user_msg, assistant_response)
for w in patterns.weaknesses:
    self.working_memory.add_weakness(w)
for s in patterns.strengths:
    self.working_memory.add_strength(s)
```

## Component 2: Style Drift

### 2A: Relationship-Based Familiarity

Track conversation depth and adjust warmth over time.

```python
class RelationshipTracker(BaseModel):
    total_exchanges: int = 0
    relationship_phase: str = "formal"  # formal → familiar → trusted

    def record_exchange(self) -> None:
        self.total_exchanges += 1
        # Phase transitions:
        # 0-10 exchanges: "formal" (professional, structured)
        # 11-50 exchanges: "familiar" (warmer, some casual language)
        # 51+ exchanges: "trusted" (comfortable, personalized)
```

**System prompt modifiers by phase:**
- Formal: "Maintain a professional, encouraging tone."
- Familiar: "You know this learner well. Be warm and personable."
- Trusted: "You're a trusted coach. Be candid and personal when helpful."

### 2B: Effectiveness-Weighted Drift

Track what coaching styles lead to engagement and drift toward them.

```python
class EffectivenessTracker(BaseModel):
    style_outcomes: dict[str, int] = {}  # style_config -> cumulative_score

    def record_outcome(self, style: str, engagement: str) -> None:
        # engagement: "high" = +2, "medium" = +0, "low" = -1
        # Track which style combinations work best

    def get_recommended_style(self) -> Optional[StyleRecommendation]:
        # Return style config with highest cumulative score
        # Only if confidence threshold met (min 5 samples)
```

**Drift mechanism:** Every 10 exchanges, check top-performing styles and nudge `current_style` toward them by one step.

## Architecture

### New Files

```
interview_prep_coach/
├── evolution/                    # NEW
│   ├── __init__.py
│   ├── pattern_extractor.py     # AI-powered insight extraction
│   ├── relationship_tracker.py  # Familiarity phase tracking
│   └── effectiveness.py         # Style outcome correlation
│
├── conversation/
│   └── session.py               # MODIFIED - integrates evolution
```

### Modified send_message() Flow

```
1. User sends message
2. Build context + call Claude for response
3. Save response to thread
4. [NEW] Extract patterns → update working_memory
5. [NEW] Record exchange → update relationship phase
6. [NEW] Record engagement → update effectiveness scores
7. [NEW] Every 10 exchanges: apply style drift
8. Save state
9. Return response
```

### Efficiency

- Pattern extraction uses Claude Haiku (fast, cheap)
- Small prompt (~200 tokens)
- Adds minimal latency (~500ms)
- Evolution happens inline, no background processes

## Data Models

### Evolution State (added to storage)

```python
class EvolutionState(BaseModel):
    relationship: RelationshipTracker = Field(default_factory=RelationshipTracker)
    effectiveness: EffectivenessTracker = Field(default_factory=EffectivenessTracker)
```

This gets persisted alongside working memory.

## Success Criteria

- After 5+ conversations, Scout correctly identifies 2+ weak areas
- Relationship phase advances naturally with usage
- Style drift correlates with user engagement patterns
- User feels Scout "knows them better" over time
