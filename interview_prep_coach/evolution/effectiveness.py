"""Style effectiveness tracking for drift."""

from typing import Optional
from pydantic import BaseModel, Field


class EffectivenessTracker(BaseModel):
    """Tracks which style combinations lead to better engagement."""

    style_outcomes: dict[str, int] = Field(default_factory=dict)
    _sample_counts: dict[str, int] = {}

    def record_outcome(self, style: str, engagement: str) -> None:
        """Record engagement outcome for a style configuration.

        Args:
            style: Style configuration string (e.g., "collaborative:medium")
            engagement: Engagement level ("high", "medium", "low")
        """
        scores = {"high": 2, "medium": 0, "low": -1}
        delta = scores.get(engagement, 0)

        if style not in self.style_outcomes:
            self.style_outcomes[style] = 0
        self.style_outcomes[style] += delta

        # Track sample count separately (not persisted)
        if not hasattr(self, "_sample_counts"):
            self._sample_counts = {}
        self._sample_counts[style] = self._sample_counts.get(style, 0) + 1

    def get_recommended_style(self, min_samples: int = 5) -> Optional[str]:
        """Get the style with highest effectiveness score.

        Args:
            min_samples: Minimum samples required for recommendation

        Returns:
            Style string with highest score, or None if insufficient data
        """
        if not hasattr(self, "_sample_counts"):
            return None

        qualified_styles = [
            style for style, count in self._sample_counts.items()
            if count >= min_samples and style in self.style_outcomes
        ]

        if not qualified_styles:
            return None

        return max(qualified_styles, key=lambda s: self.style_outcomes.get(s, 0))
