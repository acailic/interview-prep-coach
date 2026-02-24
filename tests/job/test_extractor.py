"""Tests for job posting extraction."""

import pytest
from unittest.mock import Mock
from interview_prep_coach.job.extractor import JobExtractor
from interview_prep_coach.job.context import JobContext


class TestJobExtractor:
    """Tests for job posting extraction."""

    def test_extract_from_text(self, monkeypatch):
        """Should extract job context from posting text."""
        mock_response = Mock()
        mock_response.content = [Mock(text='''{
            "company": "TechCorp",
            "position": "Senior Engineer",
            "requirements": ["5+ years Python", "Distributed systems experience"],
            "tech_stack": ["Python", "Kubernetes", "PostgreSQL"],
            "key_skills": ["System design", "Mentorship"]
        }''')]

        extractor = JobExtractor(api_key="test-key")
        monkeypatch.setattr(
            extractor.client.messages,
            "create",
            Mock(return_value=mock_response)
        )

        result = extractor.extract("TechCorp is hiring a Senior Engineer...")
        assert isinstance(result, JobContext)
        assert result.company == "TechCorp"
        assert result.position == "Senior Engineer"
        assert "Python" in result.tech_stack

    def test_extract_handles_malformed_response(self, monkeypatch):
        """Should handle malformed AI response gracefully."""
        mock_response = Mock()
        mock_response.content = [Mock(text="not valid json")]

        extractor = JobExtractor(api_key="test-key")
        monkeypatch.setattr(
            extractor.client.messages,
            "create",
            Mock(return_value=mock_response)
        )

        result = extractor.extract("Some job posting")
        assert result.company == "Unknown Company"
        assert result.position == "Unknown Position"
