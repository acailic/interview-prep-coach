"""Tests for coaching style manager."""

import pytest
from interview_prep_coach.coaching.style_manager import (
    CoachingStyle,
    StyleDimension,
    StyleManager,
)


class TestCoachingStyle:
    def test_default_style(self):
        style = CoachingStyle()
        assert style.directness == "medium"
        assert style.encouragement == "measured"
        assert style.approach == "collaborative"
        assert style.depth == "thorough"

    def test_custom_style(self):
        style = CoachingStyle(directness="high", encouragement="challenging")
        assert style.directness == "high"
        assert style.encouragement == "challenging"

    def test_valid_directness(self):
        style = CoachingStyle()
        assert style.is_valid_directness("low")
        assert style.is_valid_directness("medium")
        assert style.is_valid_directness("high")
        assert not style.is_valid_directness("extreme")

    def test_valid_encouragement(self):
        style = CoachingStyle()
        assert style.is_valid_encouragement("cheerleader")
        assert style.is_valid_encouragement("measured")
        assert style.is_valid_encouragement("challenging")
        assert not style.is_valid_encouragement("neutral")

    def test_valid_approach(self):
        style = CoachingStyle()
        assert style.is_valid_approach("socratic")
        assert style.is_valid_approach("instructional")
        assert style.is_valid_approach("collaborative")
        assert not style.is_valid_approach("mixed")

    def test_valid_depth(self):
        style = CoachingStyle()
        assert style.is_valid_depth("concise")
        assert style.is_valid_depth("thorough")
        assert not style.is_valid_depth("medium")


class TestStyleManager:
    def test_default_manager(self):
        manager = StyleManager()
        assert manager.current_style.directness == "medium"
        assert len(manager.effective_styles) == 0

    def test_adjust_directness(self):
        manager = StyleManager()
        manager.adjust(StyleDimension.DIRECTNESS, "high")
        assert manager.current_style.directness == "high"

        manager.adjust(StyleDimension.DIRECTNESS, "low")
        assert manager.current_style.directness == "low"

    def test_adjust_encouragement(self):
        manager = StyleManager()
        manager.adjust(StyleDimension.ENCOURAGEMENT, "cheerleader")
        assert manager.current_style.encouragement == "cheerleader"

    def test_adjust_approach(self):
        manager = StyleManager()
        manager.adjust(StyleDimension.APPROACH, "socratic")
        assert manager.current_style.approach == "socratic"

    def test_adjust_depth(self):
        manager = StyleManager()
        manager.adjust(StyleDimension.DEPTH, "concise")
        assert manager.current_style.depth == "concise"

    def test_adjust_ignores_invalid(self):
        manager = StyleManager()
        original = manager.current_style.directness
        manager.adjust(StyleDimension.DIRECTNESS, "invalid_value")
        assert manager.current_style.directness == original

    def test_learn_from_feedback_more_direct(self):
        manager = StyleManager()
        manager.learn_from_feedback("be more direct")
        assert manager.current_style.directness == "high"

    def test_learn_from_feedback_too_harsh(self):
        manager = StyleManager()
        manager.current_style.directness = "high"
        manager.learn_from_feedback("too harsh")
        assert manager.current_style.directness == "low"

    def test_learn_from_feedback_more_encouraging(self):
        manager = StyleManager()
        manager.learn_from_feedback("be more encouraging")
        assert manager.current_style.encouragement == "cheerleader"

    def test_learn_from_feedback_too_positive(self):
        manager = StyleManager()
        manager.current_style.encouragement = "cheerleader"
        manager.learn_from_feedback("too positive")
        assert manager.current_style.encouragement == "challenging"

    def test_learn_from_feedback_push_harder(self):
        manager = StyleManager()
        manager.learn_from_feedback("push me harder")
        assert manager.current_style.encouragement == "challenging"

    def test_learn_from_feedback_give_answer(self):
        manager = StyleManager()
        manager.learn_from_feedback("tell me the answer")
        assert manager.current_style.approach == "instructional"

    def test_learn_from_feedback_socratic(self):
        manager = StyleManager()
        manager.learn_from_feedback("guide me through this")
        assert manager.current_style.approach == "socratic"

    def test_learn_from_feedback_collaborative(self):
        manager = StyleManager()
        manager.adjust(StyleDimension.APPROACH, "instructional")
        manager.learn_from_feedback("let's work together")
        assert manager.current_style.approach == "collaborative"

    def test_learn_from_feedback_brief(self):
        manager = StyleManager()
        manager.learn_from_feedback("be more brief")
        assert manager.current_style.depth == "concise"

    def test_learn_from_feedback_too_long(self):
        manager = StyleManager()
        manager.learn_from_feedback("too wordy")
        assert manager.current_style.depth == "concise"

    def test_learn_from_feedback_detailed(self):
        manager = StyleManager()
        manager.adjust(StyleDimension.DEPTH, "concise")
        manager.learn_from_feedback("give me more detail")
        assert manager.current_style.depth == "thorough"

    def test_learn_from_feedback_explicit_adds_effective(self):
        manager = StyleManager()
        manager.learn_from_feedback("be more direct", explicit=True)
        assert "directness:high" in manager.effective_styles

    def test_record_outcome_improved(self):
        manager = StyleManager()
        manager.record_outcome("directness:high", improved=True)
        assert "directness:high" in manager.effective_styles

    def test_record_outcome_not_improved(self):
        manager = StyleManager()
        manager.effective_styles.append("directness:high")
        manager.record_outcome("directness:high", improved=False)
        assert "directness:high" not in manager.effective_styles

    def test_get_system_prompt_modifier(self):
        manager = StyleManager()
        modifier = manager.get_system_prompt_modifier()
        assert "balanced" in modifier
        assert "detailed" in modifier

    def test_get_system_prompt_modifier_high_directness(self):
        manager = StyleManager()
        manager.adjust(StyleDimension.DIRECTNESS, "high")
        modifier = manager.get_system_prompt_modifier()
        assert "direct" in modifier.lower() or "straightforward" in modifier.lower()

    def test_get_system_prompt_modifier_cheerleader(self):
        manager = StyleManager()
        manager.adjust(StyleDimension.ENCOURAGEMENT, "cheerleader")
        modifier = manager.get_system_prompt_modifier()
        assert "enthusiastic" in modifier.lower() or "celebrate" in modifier.lower()

    def test_get_system_prompt_modifier_socratic(self):
        manager = StyleManager()
        manager.adjust(StyleDimension.APPROACH, "socratic")
        modifier = manager.get_system_prompt_modifier()
        assert "question" in modifier.lower() or "discover" in modifier.lower()

    def test_get_system_prompt_modifier_concise(self):
        manager = StyleManager()
        manager.adjust(StyleDimension.DEPTH, "concise")
        modifier = manager.get_system_prompt_modifier()
        assert "brief" in modifier.lower() or "concise" in modifier.lower()
