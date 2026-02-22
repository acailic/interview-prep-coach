# Conversation-First Redesign - Design Document

**Date:** 2026-02-23
**Status:** Approved
**Goal:** Transform interview-prep-coach from transactional Q&A tool to an AI coach that knows you deeply and evolves with you

## Problem Statement

The current tool is transactional: each practice session starts fresh, feedback is generic, and there's no continuity. Users want a coach that:

1. **Remembers everything** - Past answers, what worked, growth over time
2. **Adapts to them** - Learns their coaching style preferences
3. **Feels like real coaching** - Iterative refinement, scenario exploration, genuine dialogue
4. **Has soul** - Scout's identity persists and evolves through the relationship

## Core Insight

> The conversation IS the memory. Instead of sessions and scores, build one growing conversation thread where Scout accumulates understanding of the user over time.

## Architecture Shift

```
Current:
  Session 1: Question → Answer → Score → Done
  Session 2: Question → Answer → Score → Done (fresh start)
  Session 3: Question → Answer → Score → Done (fresh start)

New:
  One conversation thread that grows over time

  User initiates → Scout greets with context → Natural coaching dialogue
  Scout remembers everything → Adapts style → Evolves with user
```

## Component 1: Memory System

**Four layers of memory:**

```
Conversation Layers:
├── Active Context (last ~20 exchanges)
│   └── Full conversation - everything recent
│
├── Working Memory (summarized)
│   ├── Current interview prep details
│   ├── Recent practice history
│   ├── Active weaknesses being addressed
│   └── Style preferences
│
├── Long-term Memory (semantic search)
│   ├── All past interviews + outcomes
│   ├── Every practice answer ever given
│   ├── Feedback that resonated
│   └── Coaching patterns that worked
│
└── Identity Layer (permanent)
    ├── Scout's core values
    ├── User's co-created preferences
    └── Relationship history
```

**How it works:**
1. Each message sends: recent conversation + working memory + relevant long-term memories
2. After each session: extract insights → update working memory, store in long-term
3. Smart retrieval: semantic search pulls relevant history when topics come up

**Technical choices:**
- Storage: SQLite + embeddings for semantic search
- Context window: Last 20 exchanges + compressed summary
- Conversation state: Single thread file per user

## Component 2: Adaptive Coaching

**Coaching style dimensions:**

| Dimension | Spectrum |
|-----------|----------|
| Feedback Directness | Gentle → Direct → Tough love |
| Encouragement Style | Cheerleader → Measured → Challenge-focused |
| Questioning Approach | Socratic → Instructional → Collaborative |
| Depth Preference | Concise → Thorough |

**How adaptation happens:**

1. **Implicit learning:**
   - User ignores gentle feedback → Scout tries more direct
   - Scores improve after collaborative sessions → Scout emphasizes that style
   - User asks "what do you really think?" → Scout learns to be more honest

2. **Explicit shaping:**
   - User: "Be more direct with me" → Scout adapts permanently
   - User: "That was too harsh" → Scout dials it back

3. **Pattern recognition:**
   - Scout tracks which coaching approaches correlate with improvement
   - Emphasizes effective approaches for this specific user

## Component 3: Interaction Patterns

### Mode 1: Iterative Refinement

Work on answers together, like editing a draft:
- Multiple passes on same answer
- Scout tracks which version is "current best"
- Can return to any answer days later to improve
- Scout suggests what to work on ("try the impact part again")

### Mode 2: Scenario Exploration

"What if they ask X?" - Role-play and simulation:
- Open-ended "what if" exploration
- Scout plays interviewer role
- Brainstorming + practice combined
- Builds confidence for unexpected questions

## Component 4: Technical Architecture

```
interview_prep_coach/
├── conversation/               # NEW
│   ├── thread.py              # Conversation thread management
│   ├── memory.py              # Memory layers
│   ├── context_builder.py     # Assembles context for each AI call
│   └── summarizer.py          # Compresses old conversation
│
├── coaching/                   # NEW
│   ├── style_manager.py       # User's coaching preferences
│   ├── effectiveness.py       # Learns what coaching works
│   └── feedback_engine.py     # Personalized feedback
│
├── modes/                      # EVOLVED
│   ├── iterative.py           # Refinement mode
│   ├── scenario.py            # What-if exploration
│   └── review.py              # Review past answers
│
├── cli.py                      # SIMPLIFIED
└── ...
```

**CLI simplification:**

```bash
# Old: Multiple commands
interview-prep practice --category behavioral
interview-prep practice --timed
interview-prep progress

# New: One conversation entry point
interview-prep chat

# Scout greets with context, user drives from there
```

## Key Design Principles

1. **Student-initiated** - Scout never pushes/schedules, always responds
2. **Conversation is memory** - No separate session tracking, just one thread
3. **Co-created identity** - User shapes Scout's style over time
4. **Learning from outcomes** - Track what coaching leads to success
5. **Soul persists** - Scout's core values stay fixed while style adapts

## Migration Path

1. Keep existing models (QuestionAttempt, PracticeSession, etc.)
2. Add conversation layer on top
3. Build memory system with SQLite + embeddings
4. Implement adaptive coaching style tracking
5. Simplify CLI to single `chat` entry point
6. Gradually deprecate session-based commands

## Success Criteria

- Scout greets user with relevant context from their history
- User can shape Scout's coaching style through feedback
- Answers can be refined over multiple passes
- "What if" scenarios feel like genuine role-play
- After months of use, Scout feels like a coach who truly knows you
