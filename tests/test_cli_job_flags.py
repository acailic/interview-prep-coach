"""Tests for job-related CLI flags."""

from click.testing import CliRunner
from interview_prep_coach.cli import main


class TestChatJobFlags:
    """Tests for --job and --job-url flags."""

    def test_chat_help_shows_job_flags(self):
        """Help should show --job and --job-url options."""
        runner = CliRunner()
        result = runner.invoke(main, ["chat", "--help"])
        assert "--job" in result.output
        assert "--job-url" in result.output
