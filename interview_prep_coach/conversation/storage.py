"""File-based persistence for conversation data."""

import json
from pathlib import Path
from typing import Optional

from .memory import WorkingMemory
from .thread import ConversationThread


class MemoryStorage:
    """File-based storage for conversation threads and working memory."""

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _thread_path(self, user_id: str) -> Path:
        return self.data_dir / f"{user_id}_thread.json"

    def _memory_path(self, user_id: str) -> Path:
        return self.data_dir / f"{user_id}_memory.json"

    def save_thread(self, thread: ConversationThread) -> None:
        path = self._thread_path(thread.user_id)
        data = thread.model_dump(mode="json")
        path.write_text(json.dumps(data, indent=2, default=str))

    def load_thread(self, user_id: str) -> Optional[ConversationThread]:
        path = self._thread_path(user_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return ConversationThread.model_validate(data)

    def save_working_memory(self, user_id: str, memory: WorkingMemory) -> None:
        path = self._memory_path(user_id)
        data = memory.model_dump(mode="json")
        path.write_text(json.dumps(data, indent=2))

    def load_working_memory(self, user_id: str) -> Optional[WorkingMemory]:
        path = self._memory_path(user_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return WorkingMemory.model_validate(data)

    def save_evolution_state(self, user_id: str, state: "EvolutionState") -> None:
        """Save evolution state to disk."""
        path = self.data_dir / "evolution" / f"{user_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(state.model_dump_json(indent=2))

    def load_evolution_state(self, user_id: str) -> Optional["EvolutionState"]:
        """Load evolution state from disk."""
        path = self.data_dir / "evolution" / f"{user_id}.json"
        if not path.exists():
            return None

        from interview_prep_coach.evolution.state import EvolutionState
        return EvolutionState.model_validate_json(path.read_text())

    def list_users(self) -> list[str]:
        users = set()
        for path in self.data_dir.glob("*_thread.json"):
            user_id = path.stem.replace("_thread", "")
            users.add(user_id)
        for path in self.data_dir.glob("*_memory.json"):
            user_id = path.stem.replace("_memory", "")
            users.add(user_id)
        return sorted(users)
