# pytest lash/plugins/sched/tests/test_cli.py
from click.testing import CliRunner
from lash.plugins.sched.cli import sched


class TestRunCmd:
    def test_no_time_returns_error(self):
        runner = CliRunner()
        result = runner.invoke(sched, ['run', 'echo hello'])
        assert result.exit_code == 0
        assert 'Error' in result.output

    def test_zero_time_explicit(self):
        runner = CliRunner()
        result = runner.invoke(sched, ['run', 'echo hello', '0', '0', '0'])
        assert result.exit_code == 0
        assert 'Error: Time delay is not defined' in result.output


class TestExecCmd:
    def test_invalid_format_too_few_parts(self):
        runner = CliRunner()
        result = runner.invoke(sched, ['exec', '10:30', 'echo hello'])
        assert result.exit_code == 0
        assert 'syntax incorrect' in result.output

    def test_invalid_format_non_digits(self):
        runner = CliRunner()
        result = runner.invoke(sched, ['exec', 'ab:cd:ef', 'echo hello'])
        assert result.exit_code == 0
        assert 'syntax incorrect' in result.output

    def test_invalid_format_four_parts(self):
        runner = CliRunner()
        result = runner.invoke(sched, ['exec', '10:30:00:00', 'echo hello'])
        assert result.exit_code == 0
        assert 'syntax incorrect' in result.output
