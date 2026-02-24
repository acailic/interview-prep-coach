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
