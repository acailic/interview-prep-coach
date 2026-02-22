"""Data models for interview practice engine."""

from datetime import date
from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from pydantic import Field


class PracticeMode(str, Enum):
    """Practice session modes."""

    focused = "focused"
    mixed = "mixed"
    timed = "timed"
    review = "review"


class QuestionCategory(str, Enum):
    """Question category types."""

    behavioral = "behavioral"
    technical = "technical"
    system_design = "system_design"
    coding = "coding"


class InterviewOutcome(str, Enum):
    """Interview outcome status."""

    pending = "pending"
    offer = "offer"
    rejected = "rejected"
    withdrawn = "withdrawn"


class QuestionAttempt(BaseModel):
    """Single question attempt with answer and feedback.

    Attributes:
        question_id: Unique identifier for the question
        question_text: The actual question text
        category: Question category
        user_answer: User's answer to the question
        scout_feedback: AI-generated feedback on the answer
        score: Score from 0-10
        weak_areas: List of identified weak areas
        attempted_at: When the attempt was made
        retry_of: ID of original attempt if this is a retry
    """

    question_id: str
    question_text: str
    category: QuestionCategory
    user_answer: str
    scout_feedback: str
    score: float = Field(ge=0.0, le=10.0)
    weak_areas: list[str] = Field(default_factory=list)
    attempted_at: datetime = Field(default_factory=datetime.now)
    retry_of: str | None = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q-001",
                "question_text": "Tell me about a time you handled conflict",
                "category": "behavioral",
                "user_answer": "In my previous role...",
                "scout_feedback": "Good structure, consider adding more specific outcomes",
                "score": 7.5,
                "weak_areas": ["specific_metrics", "outcome_focus"],
                "attempted_at": "2025-01-15T10:30:00",
                "retry_of": None,
            }
        }


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
    """

    session_id: str
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = Field(default=None)
    mode: PracticeMode
    category_filter: str | None = Field(default=None)
    time_limit_seconds: int | None = Field(default=None)
    questions: list[QuestionAttempt] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess-123",
                "started_at": "2025-01-15T09:00:00",
                "completed_at": "2025-01-15T09:45:00",
                "mode": "focused",
                "category_filter": "behavioral",
                "time_limit_seconds": 1800,
                "questions": [],
            }
        }


class ProgressSummary(BaseModel):
    """Aggregated progress across all practice.

    Attributes:
        total_sessions: Total number of practice sessions
        total_questions_practiced: Total questions attempted
        avg_score: Average score across all attempts
        category_scores: Average score by category
        weak_areas: Identified areas needing improvement
        improvement_trend: Overall trend direction
    """

    total_sessions: int = Field(default=0)
    total_questions_practiced: int = Field(default=0)
    avg_score: float = Field(default=0.0)
    category_scores: dict[str, float] = Field(default_factory=dict)
    weak_areas: list[str] = Field(default_factory=list)
    improvement_trend: str = Field(default="stable")

    class Config:
        json_schema_extra = {
            "example": {
                "total_sessions": 15,
                "total_questions_practiced": 47,
                "avg_score": 7.2,
                "category_scores": {
                    "behavioral": 7.8,
                    "technical": 6.5,
                    "system_design": 7.0,
                    "coding": 7.5,
                },
                "weak_areas": ["system_design_scaling", "technical_concurrency"],
                "improvement_trend": "improving",
            }
        }


class PostInterviewLog(BaseModel):
    """Capture from a real interview.

    Attributes:
        interview_date: Date of the interview
        company: Company name
        position: Position title
        questions_asked: Questions asked during the interview
        what_went_well: Things that went well
        what_stumped: Questions or topics that were challenging
        style_notes: Notes about interviewer style or process
        outcome: Final outcome of the interview
    """

    interview_date: date
    company: str
    position: str
    questions_asked: list[str] = Field(default_factory=list)
    what_went_well: list[str] = Field(default_factory=list)
    what_stumped: list[str] = Field(default_factory=list)
    style_notes: str | None = Field(default=None)
    outcome: InterviewOutcome | None = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "interview_date": "2025-01-20",
                "company": "TechCorp",
                "position": "Senior Software Engineer",
                "questions_asked": [
                    "Tell me about yourself",
                    "Design a rate limiter",
                ],
                "what_went_well": ["System design structure", "Clear communication"],
                "what_stumped": ["Distributed caching specifics"],
                "style_notes": "Interviewer focused heavily on trade-offs",
                "outcome": "pending",
            }
        }


class PracticeQuestion(BaseModel):
    """A practice question for interview prep.

    Attributes:
        question: The question text
        category: Question category (behavioral, technical, etc.)
        difficulty: Difficulty level (easy, medium, hard)
        notes: Optional hints or notes about the question
    """

    question: str
    category: str = "behavioral"
    difficulty: str = "medium"
    notes: str | None = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Tell me about a time you had to disagree with your manager",
                "category": "behavioral",
                "difficulty": "medium",
                "notes": "Focus on constructive approach and outcome",
            }
        }


class StudyItem(BaseModel):
    """A study item in a prep guide.

    Attributes:
        topic: The topic to study
        description: Optional description
        estimated_hours: Estimated time to complete
        priority: Priority level (1-10)
        completed: Whether this item is completed
    """

    topic: str
    description: str | None = Field(default=None)
    estimated_hours: float | None = Field(default=None)
    priority: int = Field(default=5, ge=1, le=10)
    completed: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "System Design Fundamentals",
                "description": "Review CAP theorem, consistency models",
                "estimated_hours": 2.0,
                "priority": 8,
                "completed": False,
            }
        }


class PrepGuide(BaseModel):
    """Interview preparation guide generated for a target role.

    Attributes:
        study_plan: List of study items to prepare
        practice_questions: List of practice questions
        talking_points: Key points to remember for interviews
        questions_to_ask: Questions to ask the interviewer
        key_reminders: Important reminders for interview day
        total_estimated_hours: Total prep time estimate
    """

    study_plan: list[StudyItem] = Field(default_factory=list)
    practice_questions: list[PracticeQuestion] = Field(default_factory=list)
    talking_points: list[str] = Field(default_factory=list)
    questions_to_ask: list[str] = Field(default_factory=list)
    key_reminders: list[str] = Field(default_factory=list)
    total_estimated_hours: float = 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "study_plan": [],
                "practice_questions": [],
                "talking_points": ["Led team of 5 engineers", "Scaled system to 1M users"],
                "questions_to_ask": ["What does success look like in this role?"],
                "key_reminders": ["Use STAR method for behavioral questions"],
                "total_estimated_hours": 10.0,
            }
        }
