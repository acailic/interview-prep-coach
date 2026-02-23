"""Relationship phase tracking for style drift."""

from pydantic import BaseModel, Field


class RelationshipTracker(BaseModel):
    """Tracks relationship depth for style drift."""

    total_exchanges: int = 0
    relationship_phase: str = "formal"  # formal → familiar → trusted

    def record_exchange(self) -> None:
        """Record a conversation exchange and update phase if needed."""
        self.total_exchanges += 1
        self._update_phase()

    def _update_phase(self) -> None:
        """Update relationship phase based on exchange count."""
        if self.total_exchanges >= 51:
            self.relationship_phase = "trusted"
        elif self.total_exchanges >= 11:
            self.relationship_phase = "familiar"
        else:
            self.relationship_phase = "formal"

    def get_phase_modifier(self) -> str:
        """Get system prompt modifier for current phase."""
        modifiers = {
            "formal": "Maintain a professional, encouraging tone with this new learner.",
            "familiar": "You know this learner well. Be warm and personable in your coaching.",
            "trusted": "You are a trusted coach with a strong relationship. Be candid and personal when helpful.",
        }
        return modifiers.get(self.relationship_phase, modifiers["formal"])
