"""Scoring logic for interview practice answers.

This module provides the Scorer class that calculates scores based on
feedback analysis, weak areas, and question category.

Contracts:
    - Scorer: Calculates scores from 0-10 based on multiple criteria
    - Implements ScorerProtocol from engine.py
"""

from collections import Counter

from ..models import QuestionAttempt
from ..models import QuestionCategory


class Scorer:
    """Calculates scores for interview practice answers.

    Scoring is based on:
    - Number of weak areas identified
    - Feedback sentiment indicators
    - Category-specific weighting

    Example:
        >>> scorer = Scorer()
        >>> score = scorer.calculate_score(
        ...     question={"text": "...", "category": "behavioral"},
        ...     answer="My answer...",
        ...     feedback="Good structure but needs more specificity..."
        ... )
        >>> print(f"Score: {score}/10")
    """

    CATEGORY_WEIGHTS = {
        QuestionCategory.behavioral: {
            "structure": 0.25,
            "specificity": 0.25,
            "clarity": 0.25,
            "impact": 0.25,
        },
        QuestionCategory.technical: {
            "accuracy": 0.30,
            "depth": 0.25,
            "clarity": 0.25,
            "communication": 0.20,
        },
        QuestionCategory.system_design: {
            "tradeoffs": 0.25,
            "scalability": 0.25,
            "structure": 0.25,
            "practicality": 0.25,
        },
        QuestionCategory.coding: {
            "approach": 0.25,
            "edge_cases": 0.25,
            "communication": 0.25,
            "efficiency": 0.25,
        },
    }

    POSITIVE_INDICATORS = [
        "excellent",
        "great",
        "strong",
        "good",
        "well",
        "clear",
        "effective",
        "solid",
        "polished",
        "thorough",
        "comprehensive",
        "impressive",
    ]

    NEGATIVE_INDICATORS = [
        "weak",
        "poor",
        "lacking",
        "missing",
        "unclear",
        "confusing",
        "incomplete",
        "insufficient",
        "vague",
        "needs improvement",
        "should include",
        "consider adding",
    ]

    def __init__(self):
        """Initialize the scorer."""
        pass

    def calculate_score(
        self,
        question: dict,
        answer: str,
        feedback: str,
        hard_mode: bool = False,
    ) -> float:
        """Calculate a score for the answer.

        Args:
            question: Question dict with 'text' and 'category' keys
            answer: User's answer text
            feedback: Feedback text from FeedbackAnalyzer
            hard_mode: If True, use stricter scoring thresholds

        Returns:
            Score from 0.0 to 10.0
        """
        if not answer or not answer.strip():
            return 0.0

        category_str = question.get("category", "behavioral")
        try:
            category = QuestionCategory(category_str)
        except ValueError:
            category = QuestionCategory.behavioral

        weak_areas = self._extract_weak_areas_from_feedback(feedback)

        return self.score_answer(feedback, weak_areas, category, hard_mode)

    def score_answer(
        self,
        feedback: str,
        weak_areas: list[str],
        category: QuestionCategory,
        hard_mode: bool = False,
    ) -> float:
        """Calculate a score from 0-10 based on feedback and weak areas.

        Args:
            feedback: The feedback text from FeedbackAnalyzer
            weak_areas: List of identified weak areas
            category: Question category (affects scoring weights)
            hard_mode: If True, use stricter scoring thresholds

        Returns:
            Score from 0.0 to 10.0
        """
        base_score = 4.0 if hard_mode else 7.0

        sentiment_score = self._analyze_sentiment(feedback, hard_mode)
        weak_area_penalty = self._calculate_weak_area_penalty(weak_areas, hard_mode)

        raw_score = base_score + sentiment_score - weak_area_penalty

        return max(0.0, min(10.0, raw_score))

    def calculate_category_average(
        self,
        attempts: list[QuestionAttempt],
        category: QuestionCategory,
    ) -> float:
        """Calculate average score for a specific category.

        Args:
            attempts: List of question attempts
            category: Category to filter by

        Returns:
            Average score for the category, or 0.0 if no attempts.
        """
        category_attempts = [
            a for a in attempts
            if a.category == category and a.score > 0
        ]

        if not category_attempts:
            return 0.0

        total = sum(a.score for a in category_attempts)
        return round(total / len(category_attempts), 1)

    def detect_weak_areas(
        self,
        attempts: list[QuestionAttempt],
    ) -> list[str]:
        """Detect weak areas from patterns in feedback.

        Args:
            attempts: List of question attempts with weak_areas

        Returns:
            List of weak areas sorted by frequency.
        """
        all_weak_areas: list[str] = []
        for attempt in attempts:
            all_weak_areas.extend(attempt.weak_areas)

        if not all_weak_areas:
            return []

        counter = Counter(all_weak_areas)
        return [area for area, _ in counter.most_common()]

    def calculate_session_score(
        self,
        attempts: list[QuestionAttempt],
    ) -> float:
        """Calculate overall session score.

        Args:
            attempts: List of question attempts in the session

        Returns:
            Average score across all attempts, or 0.0 if empty.
        """
        if not attempts:
            return 0.0

        total = sum(a.score for a in attempts)
        return round(total / len(attempts), 1)

    def _analyze_sentiment(self, feedback: str, hard_mode: bool = False) -> float:
        """Analyze feedback sentiment and return score adjustment.

        Args:
            feedback: Feedback text to analyze
            hard_mode: If True, cap adjustment at ±1.0 instead of ±2.0

        Returns:
            Score adjustment from -2.0 to +2.0 (or ±1.0 in hard mode)
        """
        if not feedback:
            return 0.0

        lower_feedback = feedback.lower()

        positive_count = sum(
            1 for indicator in self.POSITIVE_INDICATORS
            if indicator in lower_feedback
        )
        negative_count = sum(
            1 for indicator in self.NEGATIVE_INDICATORS
            if indicator in lower_feedback
        )

        net_sentiment = positive_count - negative_count

        if hard_mode:
            return max(-1.0, min(1.0, net_sentiment * 0.25))
        else:
            return max(-2.0, min(2.0, net_sentiment * 0.5))

    def _calculate_weak_area_penalty(self, weak_areas: list[str], hard_mode: bool = False) -> float:
        """Calculate score penalty based on number of weak areas.

        Args:
            weak_areas: List of identified weak areas
            hard_mode: If True, use steeper penalties (2.0/4.0/6.0 vs 1.0/2.0/3.0)

        Returns:
            Penalty from 0.0 to 5.0 (normal) or 0.0 to 6.0 (hard mode)
        """
        if not weak_areas:
            return 0.0

        num_weak_areas = len(weak_areas)

        if hard_mode:
            # Hard mode: steeper penalties
            if num_weak_areas == 1:
                return 2.0
            elif num_weak_areas == 2:
                return 4.0
            else:
                return 6.0
        else:
            # Normal mode
            if num_weak_areas == 1:
                return 1.0
            elif num_weak_areas == 2:
                return 2.0
            elif num_weak_areas == 3:
                return 3.0
            else:
                return min(5.0, 3.0 + (num_weak_areas - 3) * 0.5)

    def _extract_weak_areas_from_feedback(self, feedback: str) -> list[str]:
        """Extract weak area indicators from feedback text.

        Args:
            feedback: Feedback text to analyze

        Returns:
            List of detected weak areas.
        """
        weak_areas = []
        lower_feedback = feedback.lower()

        area_keywords = {
            "structure": ["structure", "organized", "star method", "narrative"],
            "specificity": ["specific", "concrete", "example", "metric", "quantify"],
            "clarity": ["clear", "concise", "confusing", "unclear", "rambling"],
            "depth": ["depth", "surface", "deep", "thorough", "detail"],
            "impact": ["impact", "result", "outcome", "achievement"],
            "accuracy": ["correct", "accurate", "wrong", "error", "mistake"],
            "tradeoffs": ["trade-off", "tradeoff", "alternative", "consider"],
            "scalability": ["scale", "scalability", "growth", "performance"],
            "edge_cases": ["edge case", "boundary", "corner case"],
            "efficiency": ["efficient", "complexity", "optimize", "performance"],
        }

        for area, keywords in area_keywords.items():
            for keyword in keywords:
                if keyword in lower_feedback:
                    negation_present = any(
                        neg in lower_feedback[max(0, lower_feedback.find(keyword) - 20):lower_feedback.find(keyword)]
                        for neg in ["not ", "lacking ", "missing ", "needs ", "should ", "improve"]
                    )
                    if negation_present:
                        weak_areas.append(area)
                        break

        return list(set(weak_areas))
