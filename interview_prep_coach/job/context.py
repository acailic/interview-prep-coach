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
