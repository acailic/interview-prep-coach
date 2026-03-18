# tests/practice/test_scorer_hard_mode.py

import pytest
from interview_prep_coach.practice.scorer import Scorer
from interview_prep_coach.models import QuestionCategory


class TestScorerHardMode:
    """Test hard mode scoring behavior."""

    def test_hard_mode_lower_base_score(self):
        """Hard mode should start with lower base score (4.0 vs 7.0)."""
        scorer = Scorer()

        # Normal mode with no weak areas and positive feedback
        normal_score = scorer.score_answer(
            feedback="Excellent answer with great clarity.",
            weak_areas=[],
            category=QuestionCategory.behavioral,
            hard_mode=False,
        )

        # Hard mode with same input
        hard_score = scorer.score_answer(
            feedback="Excellent answer with great clarity.",
            weak_areas=[],
            category=QuestionCategory.behavioral,
            hard_mode=True,
        )

        # Hard mode should be lower (4.0 base vs 7.0 base)
        assert hard_score < normal_score
        # With positive sentiment, normal ~8.5, hard ~4.5
        assert normal_score > 7.0
        assert hard_score <= 5.0  # Max is 4.0 base + 1.0 max sentiment

    def test_hard_mode_steeper_weak_area_penalties(self):
        """Hard mode should penalize weak areas more heavily."""
        scorer = Scorer()
        weak_areas = ["specificity", "structure"]

        normal_score = scorer.score_answer(
            feedback="Good attempt but needs improvement.",
            weak_areas=weak_areas,
            category=QuestionCategory.behavioral,
            hard_mode=False,
        )

        hard_score = scorer.score_answer(
            feedback="Good attempt but needs improvement.",
            weak_areas=weak_areas,
            category=QuestionCategory.behavioral,
            hard_mode=True,
        )

        # Normal: 7.0 - 2.0 (2 weak areas) = 5.0
        # Hard: 4.0 - 4.0 (2 weak areas) = 0.0
        assert normal_score >= 4.0
        assert hard_score <= 1.0

    def test_hard_mode_caps_positive_sentiment(self):
        """Hard mode should cap positive sentiment bonus at +1.0."""
        scorer = Scorer()

        # Very positive feedback
        positive_feedback = "Excellent great strong good well clear effective solid polished"

        normal_score = scorer.score_answer(
            feedback=positive_feedback,
            weak_areas=[],
            category=QuestionCategory.behavioral,
            hard_mode=False,
        )

        hard_score = scorer.score_answer(
            feedback=positive_feedback,
            weak_areas=[],
            category=QuestionCategory.behavioral,
            hard_mode=True,
        )

        # Normal can go up to 9.0 (7.0 + 2.0 max sentiment)
        # Hard maxes at 5.0 (4.0 + 1.0 max sentiment)
        assert normal_score >= 8.0
        assert hard_score <= 5.0

    def test_one_weak_area_hard_mode_penalty(self):
        """Hard mode should penalize 1 weak area by 2.0."""
        scorer = Scorer()

        score = scorer.score_answer(
            feedback="Decent answer.",
            weak_areas=["clarity"],
            category=QuestionCategory.behavioral,
            hard_mode=True,
        )

        # 4.0 base - 2.0 penalty = 2.0
        assert 1.0 <= score <= 3.0

    def test_three_weak_areas_hard_mode_penalty(self):
        """Hard mode should penalize 3+ weak areas by 6.0 (floor at 0)."""
        scorer = Scorer()

        score = scorer.score_answer(
            feedback="Needs work.",
            weak_areas=["clarity", "specificity", "structure"],
            category=QuestionCategory.behavioral,
            hard_mode=True,
        )

        # 4.0 base - 6.0 penalty + sentiment = -2.0 + sentiment
        # Even with slight negative sentiment, floor is 0.0
        assert score == 0.0

    def test_calculate_score_accepts_hard_mode(self):
        """calculate_score method should accept hard_mode parameter."""
        scorer = Scorer()

        score = scorer.calculate_score(
            question={"text": "Test", "category": "behavioral"},
            answer="My answer",
            feedback="Good work.",
            hard_mode=True,
        )

        assert isinstance(score, float)
        assert 0.0 <= score <= 10.0
