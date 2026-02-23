"""Combined evolution state for persistence."""

from pydantic import BaseModel, Field

from .relationship_tracker import RelationshipTracker
from .effectiveness import EffectivenessTracker


class EvolutionState(BaseModel):
    """Combined state for all evolution components."""

    relationship: RelationshipTracker = Field(default_factory=RelationshipTracker)
    effectiveness: EffectivenessTracker = Field(default_factory=EffectivenessTracker)

    def record_exchange(self) -> None:
        """Record a conversation exchange."""
        self.relationship.record_exchange()

    def record_style_outcome(self, style: str, engagement: str) -> None:
        """Record style effectiveness outcome."""
        self.effectiveness.record_outcome(style, engagement)
