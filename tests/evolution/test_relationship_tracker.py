"""Tests for relationship tracking."""

import pytest
from interview_prep_coach.evolution.relationship_tracker import RelationshipTracker


class TestRelationshipTracker:
    """Tests for relationship phase tracking."""

    def test_initial_state(self):
        """New tracker should start at formal phase."""
        tracker = RelationshipTracker()
        assert tracker.total_exchanges == 0
        assert tracker.relationship_phase == "formal"

    def test_record_exchange(self):
        """Recording exchange should increment count."""
        tracker = RelationshipTracker()
        tracker.record_exchange()
        assert tracker.total_exchanges == 1

    def test_phase_transition_to_familiar(self):
        """Should transition to familiar after 11 exchanges."""
        tracker = RelationshipTracker()
        for _ in range(11):
            tracker.record_exchange()
        assert tracker.relationship_phase == "familiar"

    def test_phase_transition_to_trusted(self):
        """Should transition to trusted after 51 exchanges."""
        tracker = RelationshipTracker()
        for _ in range(51):
            tracker.record_exchange()
        assert tracker.relationship_phase == "trusted"

    def test_get_phase_modifier_formal(self):
        """Formal phase should have professional modifier."""
        tracker = RelationshipTracker()
        assert "professional" in tracker.get_phase_modifier().lower()

    def test_get_phase_modifier_familiar(self):
        """Familiar phase should have warm modifier."""
        tracker = RelationshipTracker()
        tracker.relationship_phase = "familiar"
        assert "warm" in tracker.get_phase_modifier().lower()

    def test_get_phase_modifier_trusted(self):
        """Trusted phase should have candid modifier."""
        tracker = RelationshipTracker()
        tracker.relationship_phase = "trusted"
        assert "candid" in tracker.get_phase_modifier().lower()
