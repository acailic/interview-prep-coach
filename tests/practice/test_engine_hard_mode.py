# tests/practice/test_engine_hard_mode.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from interview_prep_coach.practice.engine import PracticeEngine
from interview_prep_coach.models import PracticeMode, QuestionCategory


class TestPracticeEngineHardMode:
    """Test hard mode integration in PracticeEngine."""

    @pytest.mark.asyncio
    async def test_start_session_accepts_hard_mode(self):
        """start_session should accept hard_mode parameter."""
        mock_bank = MagicMock()
        mock_tracker = MagicMock()
        mock_analyzer = AsyncMock()
        mock_scorer = MagicMock()

        mock_tracker.get_completed_question_ids.return_value = []
        mock_bank.get_questions.return_value = []

        engine = PracticeEngine(
            question_bank=mock_bank,
            progress_tracker=mock_tracker,
            feedback_analyzer=mock_analyzer,
            scorer=mock_scorer,
        )

        session = await engine.start_session(
            mode=PracticeMode.focused,
            category=QuestionCategory.behavioral,
            hard_mode=True,
        )

        assert session.hard_mode is True

    @pytest.mark.asyncio
    async def test_submit_answer_passes_hard_mode_to_analyzer(self):
        """submit_answer should pass hard_mode to feedback analyzer."""
        mock_bank = MagicMock()
        mock_tracker = MagicMock()
        mock_analyzer = AsyncMock()
        mock_scorer = MagicMock()

        mock_tracker.get_completed_question_ids.return_value = []
        mock_bank.get_questions.return_value = [
            {"id": "q1", "text": "Test question", "category": "behavioral"}
        ]
        mock_bank.get_question_by_id.return_value = {
            "id": "q1", "text": "Test question", "category": "behavioral"
        }
        mock_analyzer.analyze_answer.return_value = ("Good", 7.0, [])

        engine = PracticeEngine(
            question_bank=mock_bank,
            progress_tracker=mock_tracker,
            feedback_analyzer=mock_analyzer,
            scorer=mock_scorer,
        )

        await engine.start_session(mode=PracticeMode.focused, hard_mode=True)
        await engine.submit_answer("q1", "My answer")

        # Verify analyzer was called with hard_mode=True
        mock_analyzer.analyze_answer.assert_called_once()
        call_kwargs = mock_analyzer.analyze_answer.call_args.kwargs
        assert call_kwargs.get("hard_mode") is True
