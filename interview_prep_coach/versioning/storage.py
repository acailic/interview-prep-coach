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
