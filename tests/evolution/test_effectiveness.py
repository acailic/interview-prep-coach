"""Tests for effectiveness tracking."""

import pytest
from interview_prep_coach.evolution.effectiveness import EffectivenessTracker


class TestEffectivenessTracker:
    """Tests for style effectiveness tracking."""

    def test_initial_state(self):
        """New tracker should have empty outcomes."""
        tracker = EffectivenessTracker()
        assert tracker.style_outcomes == {}

    def test_record_high_engagement(self):
        """High engagement should add positive score."""
        tracker = EffectivenessTracker()
        tracker.record_outcome("direct:high", "high")
        assert tracker.style_outcomes["direct:high"] == 2

    def test_record_medium_engagement(self):
        """Medium engagement should add zero."""
        tracker = EffectivenessTracker()
        tracker.record_outcome("direct:high", "medium")
        assert tracker.style_outcomes["direct:high"] == 0

    def test_record_low_engagement(self):
        """Low engagement should subtract."""
        tracker = EffectivenessTracker()
        tracker.record_outcome("direct:high", "low")
        assert tracker.style_outcomes["direct:high"] == -1

    def test_cumulative_scoring(self):
        """Scores should accumulate."""
        tracker = EffectivenessTracker()
        tracker.record_outcome("collaborative:medium", "high")
        tracker.record_outcome("collaborative:medium", "high")
        tracker.record_outcome("collaborative:medium", "low")
        assert tracker.style_outcomes["collaborative:medium"] == 3  # 2 + 2 - 1

    def test_get_recommended_style_insufficient_data(self):
        """Should return None with insufficient samples."""
        tracker = EffectivenessTracker()
        tracker.record_outcome("direct:high", "high")
        result = tracker.get_recommended_style()
        assert result is None  # Only 1 sample, need 5+

    def test_get_recommended_style_sufficient_data(self):
        """Should return top style with sufficient samples."""
        tracker = EffectivenessTracker()
        # Record 5 high-engagement outcomes for collaborative
        for _ in range(5):
            tracker.record_outcome("collaborative:medium", "high")
        # Record 5 low-engagement outcomes for directive
        for _ in range(5):
            tracker.record_outcome("direct:high", "low")

        result = tracker.get_recommended_style()
        assert result == "collaborative:medium"
