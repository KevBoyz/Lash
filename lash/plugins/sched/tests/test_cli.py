# pytest lash/plugins/sched/tests/test_cli.py
from unittest.mock import patch

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


class TestAfterCmd:
    def test_runs_second_command_after_first_finishes(self):
        runner = CliRunner()
        with patch('lash.plugins.sched.cli.run_command') as mock_run_command:
            result = runner.invoke(
                sched, ['after', 'echo first', 'echo second'])

        assert result.exit_code == 0
        assert mock_run_command.call_count == 2
        assert mock_run_command.call_args_list[0].args[0] == 'echo first'
        assert mock_run_command.call_args_list[1].args[0] == 'echo second'
