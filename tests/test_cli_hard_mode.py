# tests/test_cli_hard_mode.py

from click.testing import CliRunner
from interview_prep_coach.cli import main


class TestCLIHardModeFlag:
    """Test --hard flag in CLI commands."""

    def test_practice_command_has_hard_flag(self):
        """practice command should accept --hard flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["practice", "--help"])
        assert "--hard" in result.output

    def test_chat_command_has_hard_flag(self):
        """chat command should accept --hard flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["chat", "--help"])
        assert "--hard" in result.output

    def test_quick_practice_command_has_hard_flag(self):
        """quick-practice command should accept --hard flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-practice", "--help"])
        assert "--hard" in result.output
