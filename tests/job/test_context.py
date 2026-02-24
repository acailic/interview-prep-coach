"""Tests for job context models."""

from interview_prep_coach.job.context import JobContext


class TestJobContext:
    """Tests for JobContext model."""

    def test_create_job_context(self):
        """Should create job context with all fields."""
        context = JobContext(
            company="TechCorp",
            position="Senior Engineer",
            requirements=["5+ years experience", "Distributed systems"],
            tech_stack=["Python", "Kubernetes", "PostgreSQL"],
            key_skills=["System design", "Team leadership"],
            raw_posting="Original job posting text...",
        )
        assert context.company == "TechCorp"
        assert context.position == "Senior Engineer"
        assert "Python" in context.tech_stack
        assert len(context.requirements) == 2

    def test_minimal_job_context(self):
        """Should create with minimal fields."""
        context = JobContext(
            company="StartupXYZ",
            position="Engineer",
            raw_posting="Job posting",
        )
        assert context.company == "StartupXYZ"
        assert context.requirements == []
        assert context.tech_stack == []
