"""AI-powered feedback analyzer for interview answers.

This module provides the FeedbackAnalyzer class that uses Claude to evaluate
interview answers across different question categories.

Contracts:
    - FeedbackAnalyzer: Analyzes answers with AI feedback
    - Implements FeedbackAnalyzerProtocol from engine.py
"""

import json
from typing import Any

from ..anthropic_session import ClaudeSession, SessionOptions
from ..models import QuestionCategory


class FeedbackAnalyzer:
    """Analyzes interview answers using Claude AI.

    Provides structured feedback including score, strengths, and weak areas
    based on question category-specific evaluation criteria.

    Example:
        >>> analyzer = FeedbackAnalyzer()
        >>> feedback, score, weak_areas = await analyzer.analyze_answer(
        ...     question={"text": "Tell me about a time...", "category": "behavioral"},
        ...     answer="In my previous role..."
        ... )
        >>> print(f"Score: {score}/10")
    """

    CATEGORY_PROMPTS = {
        QuestionCategory.behavioral: """You are an expert interview coach evaluating a behavioral interview answer.

Evaluate the answer for:
1. STAR Structure (Situation, Task, Action, Result) - Is there a clear narrative?
2. Specificity - Are there concrete examples with measurable outcomes?
3. Relevance - Does the answer connect to skills employers value?
4. Clarity - Is the communication clear and concise?
5. Impact - Does the result demonstrate meaningful contribution?""",

        QuestionCategory.technical: """You are an expert technical interviewer evaluating a technical answer.

Evaluate the answer for:
1. Accuracy - Is the technical information correct?
2. Depth - Does it show deep understanding, not just surface knowledge?
3. Clarity - Is the explanation clear and well-structured?
4. Practicality - Can they apply the knowledge in real scenarios?
5. Communication - Are complex concepts explained simply?""",

        QuestionCategory.system_design: """You are an expert system design interviewer evaluating a system design answer.

Evaluate the answer for:
1. Trade-off Analysis - Are alternatives considered and weighed?
2. Scalability - Does it handle growth in users/data/traffic?
3. Structure - Is there a logical approach (requirements, constraints, design)?
4. Real-world Thinking - Are practical concerns addressed (cost, latency, etc.)?
5. Communication - Are diagrams/abstractions used effectively?""",

        QuestionCategory.coding: """You are an expert coding interviewer evaluating a coding answer.

Evaluate the answer for:
1. Approach - Is the solution strategy sound?
2. Edge Cases - Are boundary conditions considered?
3. Communication - Is the thought process clearly explained?
4. Code Quality - Would the code be clean and maintainable?
5. Efficiency - Is time/space complexity appropriate?""",
    }

    def __init__(self, session_manager: Any = None):
        """Initialize the feedback analyzer.

        Args:
            session_manager: Optional session manager for profile context
                           (future: will use for personalized feedback)
        """
        self._session_manager = session_manager

    async def analyze_answer(
        self,
        question: dict,
        answer: str,
    ) -> tuple[str, float, list[str]]:
        """Analyze an answer and provide feedback.

        Args:
            question: Question dict with 'text' and 'category' keys
            answer: User's answer text

        Returns:
            Tuple of (feedback_text, score_0_to_10, list_of_weak_areas)
        """
        if not answer or not answer.strip():
            return "No answer provided. Please provide an answer to receive feedback.", 0.0, ["no_answer"]

        category_str = question.get("category", "behavioral")
        try:
            category = QuestionCategory(category_str)
        except ValueError:
            category = QuestionCategory.behavioral

        system_prompt = self._get_system_prompt(category)
        analysis_prompt = self._build_analysis_prompt(question, answer, category)

        options = SessionOptions(
            system_prompt=system_prompt,
            max_turns=1,
        )

        async with ClaudeSession(options) as claude:
            response = await claude.query(analysis_prompt)

            if not response.success:
                return self._fallback_feedback(category), 5.0, ["analysis_unavailable"]

            return self._parse_response(response.content)

    def _get_system_prompt(self, category: QuestionCategory) -> str:
        """Get the system prompt for a question category."""
        base_prompt = self.CATEGORY_PROMPTS.get(
            category,
            self.CATEGORY_PROMPTS[QuestionCategory.behavioral]
        )

        return f"""{base_prompt}

IMPORTANT: You must respond in the following JSON format only:
{{
    "feedback": "Your detailed feedback (2-3 paragraphs with specific suggestions)",
    "score": 7.5,
    "weak_areas": ["area1", "area2"],
    "strengths": ["strength1", "strength2"]
}}

Score on a 0-10 scale where:
- 0-3: Major issues, needs significant improvement
- 4-5: Below average, several areas to improve
- 6-7: Average to good, minor improvements possible
- 8-9: Very good, polished answer
- 10: Exceptional, interview-ready

Be constructive and specific in feedback. Always provide actionable suggestions."""

    def _build_analysis_prompt(
        self,
        question: dict,
        answer: str,
        category: QuestionCategory,
    ) -> str:
        """Build the analysis prompt for Claude."""
        question_text = question.get("text", "Unknown question")
        difficulty = question.get("difficulty", "medium")
        notes = question.get("notes", "")

        prompt = f"""Analyze this interview answer and provide feedback.

QUESTION: {question_text}

DIFFICULTY: {difficulty}

"""
        if notes:
            prompt += f"INTERVIEWER NOTES: {notes}\n\n"

        prompt += f"""ANSWER:
{answer}

Provide your analysis as JSON with feedback, score (0-10), weak_areas, and strengths."""

        return prompt

    def _parse_response(self, response_content: str) -> tuple[str, float, list[str]]:
        """Parse Claude's response into structured feedback."""
        try:
            json_start = response_content.find("{")
            json_end = response_content.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                return self._parse_text_response(response_content)

            json_str = response_content[json_start:json_end]
            data = json.loads(json_str)

            feedback = data.get("feedback", response_content)
            score = float(data.get("score", 5.0))
            score = max(0.0, min(10.0, score))
            weak_areas = data.get("weak_areas", [])

            if not isinstance(weak_areas, list):
                weak_areas = []

            return feedback, score, weak_areas

        except (json.JSONDecodeError, ValueError, TypeError):
            return self._parse_text_response(response_content)

    def _parse_text_response(self, text: str) -> tuple[str, float, list[str]]:
        """Fallback parser for non-JSON responses."""
        weak_areas = []

        lower_text = text.lower()
        if "structure" in lower_text and "improve" in lower_text:
            weak_areas.append("structure")
        if "specific" in lower_text and "more" in lower_text:
            weak_areas.append("specificity")
        if "clear" not in lower_text or "unclear" in lower_text:
            weak_areas.append("clarity")
        if not weak_areas:
            weak_areas = ["general"]

        return text, 6.0, weak_areas

    def _fallback_feedback(self, category: QuestionCategory) -> str:
        """Generate fallback feedback when analysis fails."""
        fallbacks = {
            QuestionCategory.behavioral: (
                "Unable to analyze your behavioral answer in detail. "
                "General tips: Use the STAR method (Situation, Task, Action, Result), "
                "be specific with metrics and outcomes, and connect your example to the job requirements."
            ),
            QuestionCategory.technical: (
                "Unable to analyze your technical answer in detail. "
                "General tips: Ensure accuracy in technical concepts, provide concrete examples, "
                "and explain your reasoning clearly."
            ),
            QuestionCategory.system_design: (
                "Unable to analyze your system design answer in detail. "
                "General tips: Start with requirements, discuss trade-offs, consider scalability, "
                "and structure your answer logically."
            ),
            QuestionCategory.coding: (
                "Unable to analyze your coding answer in detail. "
                "General tips: Explain your approach before coding, consider edge cases, "
                "communicate your thought process, and discuss time/space complexity."
            ),
        }
        return fallbacks.get(category, "Unable to analyze answer. Please try again.")
