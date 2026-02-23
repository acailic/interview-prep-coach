"""Tests for pattern extraction from conversations."""

import pytest
from interview_prep_coach.evolution.pattern_extractor import ExtractionResult, PatternExtractor


class TestExtractionResult:
    """Tests for ExtractionResult model."""

    def test_default_values(self):
        """ExtractionResult should have sensible defaults."""
        result = ExtractionResult()
        assert result.weaknesses == []
        assert result.strengths == []
        assert result.engagement_level == "medium"

    def test_with_data(self):
        """ExtractionResult should accept provided values."""
        result = ExtractionResult(
            weaknesses=["struggles with system design"],
            strengths=["good at STAR format"],
            engagement_level="high",
        )
        assert result.weaknesses == ["struggles with system design"]
        assert result.strengths == ["good at STAR format"]
        assert result.engagement_level == "high"


class TestPatternExtractor:
    """Tests for PatternExtractor."""

    def test_extract_returns_result(self):
        """extract() should return an ExtractionResult."""
        extractor = PatternExtractor(api_key="test-key")
        result = extractor.extract(
            user_message="I struggle with system design questions",
            assistant_response="Let's work on that together.",
        )
        assert isinstance(result, ExtractionResult)


class TestPatternExtractorAI:
    """Tests for AI-powered extraction."""

    def test_extract_with_real_content(self, monkeypatch):
        """extract() should parse AI response correctly."""
        mock_response = type(
            "MockResponse",
            (),
            {"content": [type("MockContent", (), {"text": '{"weaknesses": ["system design scaling"], "strengths": ["clear communication"], "engagement_level": "high"}'})]},
        )()

        def mock_create(*args, **kwargs):
            return mock_response

        extractor = PatternExtractor(api_key="test-key")
        monkeypatch.setattr(extractor.client.messages, "create", mock_create)

        result = extractor.extract(
            user_message="How do I design a distributed cache?",
            assistant_response="Great question! Let's explore caching strategies...",
        )

        assert "system design scaling" in result.weaknesses
        assert "clear communication" in result.strengths
        assert result.engagement_level == "high"
