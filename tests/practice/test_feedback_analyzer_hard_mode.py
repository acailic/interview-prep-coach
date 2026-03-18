# tests/practice/test_feedback_analyzer_hard_mode.py

import pytest
from interview_prep_coach.practice.feedback_analyzer import FeedbackAnalyzer
from interview_prep_coach.models import QuestionCategory


class TestFeedbackAnalyzerHardMode:
    """Test hard mode feedback prompts."""

    def test_get_system_prompt_includes_hard_mode_modifier(self):
        """Hard mode prompt should include critical evaluation instructions."""
        analyzer = FeedbackAnalyzer()

        normal_prompt = analyzer._get_system_prompt(QuestionCategory.behavioral, hard_mode=False)
        hard_prompt = analyzer._get_system_prompt(QuestionCategory.behavioral, hard_mode=True)

        # Hard mode should mention being honest/critical
        assert "brutally honest" in hard_prompt.lower() or "critical" in hard_prompt.lower()
        # Normal mode should be constructive
        assert "constructive" in normal_prompt.lower()

    def test_hard_mode_prompt_differs_from_normal(self):
        """Hard mode prompt should be different from normal mode."""
        analyzer = FeedbackAnalyzer()

        normal_prompt = analyzer._get_system_prompt(QuestionCategory.behavioral, hard_mode=False)
        hard_prompt = analyzer._get_system_prompt(QuestionCategory.behavioral, hard_mode=True)

        assert normal_prompt != hard_prompt

    def test_analyze_answer_accepts_hard_mode(self):
        """analyze_answer method should accept hard_mode parameter."""
        import inspect
        analyzer = FeedbackAnalyzer()
        sig = inspect.signature(analyzer.analyze_answer)
        params = list(sig.parameters.keys())

        assert "hard_mode" in params


class TestHardModePromptContent:
    """Test content of hard mode prompts."""

    def test_hard_mode_includes_score_guidance(self):
        """Hard mode should include tougher score band guidance."""
        analyzer = FeedbackAnalyzer()

        hard_prompt = analyzer._get_system_prompt(QuestionCategory.behavioral, hard_mode=True)

        # Should mention that high scores require excellence
        assert "8" in hard_prompt or "impressive" in hard_prompt.lower()
