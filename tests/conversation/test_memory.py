import pytest

from interview_prep_coach.conversation.memory import InterviewContext, WorkingMemory


class TestInterviewContext:
    def test_create_context(self):
        context = InterviewContext(
            company="Acme Corp",
            position="Senior Engineer",
            days_until_interview=3,
        )
        assert context.company == "Acme Corp"
        assert context.days_until_interview == 3

    def test_context_optional_fields(self):
        context = InterviewContext(company="Acme Corp")
        assert context.position is None


class TestWorkingMemory:
    def test_create_empty_memory(self):
        memory = WorkingMemory()
        assert memory.current_context is None
        assert len(memory.recent_weaknesses) == 0

    def test_set_interview_context(self):
        memory = WorkingMemory()
        memory.set_context(company="Acme Corp", position="Senior Engineer", days_until=3)
        assert memory.current_context.company == "Acme Corp"

    def test_track_weaknesses(self):
        memory = WorkingMemory()
        memory.add_weakness("specificity")
        memory.add_weakness("STAR structure")
        assert "specificity" in memory.recent_weaknesses

    def test_track_style_preference(self):
        memory = WorkingMemory()
        memory.set_preference("directness", "high")
        assert memory.get_preference("directness") == "high"

    def test_to_context_string(self):
        memory = WorkingMemory()
        memory.set_context(company="Acme", position="Engineer", days_until=3)
        memory.add_weakness("specificity")
        context_str = memory.to_context_string()
        assert "Acme" in context_str
        assert "specificity" in context_str
