from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from interview_prep_coach.job.context import JobContext


class InterviewContext(BaseModel):
    company: str
    position: Optional[str] = None
    days_until_interview: Optional[int] = None
    notes: list[str] = Field(default_factory=list)


class WorkingMemory(BaseModel):
    current_context: Optional[InterviewContext] = None
    recent_weaknesses: list[str] = Field(default_factory=list)
    recent_strengths: list[str] = Field(default_factory=list)
    style_preferences: dict[str, str] = Field(default_factory=dict)
    last_session_summary: Optional[str] = None
    job_context: Optional["JobContext"] = None

    def set_context(
        self,
        company: str,
        position: Optional[str] = None,
        days_until: Optional[int] = None,
    ) -> None:
        self.current_context = InterviewContext(
            company=company,
            position=position,
            days_until_interview=days_until,
        )

    def add_weakness(self, weakness: str) -> None:
        if weakness not in self.recent_weaknesses:
            self.recent_weaknesses.append(weakness)

    def add_strength(self, strength: str) -> None:
        if strength not in self.recent_strengths:
            self.recent_strengths.append(strength)

    def set_preference(self, dimension: str, value: str) -> None:
        self.style_preferences[dimension] = value

    def get_preference(self, dimension: str) -> Optional[str]:
        return self.style_preferences.get(dimension)

    def set_job_context(self, job: "JobContext") -> None:
        """Set the job context for personalized coaching."""
        self.job_context = job

    def to_context_string(self) -> str:
        parts = []

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


def _rebuild_working_memory() -> None:
    from interview_prep_coach.job.context import JobContext

    WorkingMemory.model_rebuild(_types_namespace={"JobContext": JobContext})


_rebuild_working_memory()
