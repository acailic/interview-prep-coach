"""Tests for evolution state."""

from interview_prep_coach.evolution.state import EvolutionState
from interview_prep_coach.evolution.relationship_tracker import RelationshipTracker
from interview_prep_coach.evolution.effectiveness import EffectivenessTracker


class TestEvolutionState:
    """Tests for combined evolution state."""

    def test_default_state(self):
        """EvolutionState should have default components."""
        state = EvolutionState()
        assert isinstance(state.relationship, RelationshipTracker)
        assert isinstance(state.effectiveness, EffectivenessTracker)

    def test_record_exchange(self):
        """record_exchange should delegate to relationship tracker."""
        state = EvolutionState()
        state.record_exchange()
        assert state.relationship.total_exchanges == 1

    def test_record_style_outcome(self):
        """record_style_outcome should delegate to effectiveness tracker."""
        state = EvolutionState()
        state.record_style_outcome("collaborative", "high")
        assert "collaborative" in state.effectiveness.style_outcomes
