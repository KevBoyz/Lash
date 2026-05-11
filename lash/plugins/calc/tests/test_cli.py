# pytest lash/plugins/calc/tests/test_cli.py
import pytest
from click.testing import CliRunner
from lash.plugins.calc.cli import calc


class TestProbCmd:
    def test_basic_percentage(self):
        runner = CliRunner()
        result = runner.invoke(calc, ['prob', '10', '5'])
        assert result.exit_code == 0
        assert '50.0%' in result.output

    def test_decimal_flag(self):
        runner = CliRunner()
        result = runner.invoke(calc, ['prob', '4', '1', '-d'])
        assert result.exit_code == 0
        assert '0.25' in result.output

    def test_fc_greater_than_pc_returns_error(self):
        runner = CliRunner()
        result = runner.invoke(calc, ['prob', '5', '10'])
        assert result.exit_code == 0
        assert 'not possible' in result.output

    def test_fc_greater_than_pc_does_not_compute(self):
        runner = CliRunner()
        result = runner.invoke(calc, ['prob', '5', '10'])
        assert '2.0' not in result.output  # 10/5 = 2.0 must not appear


class TestCartesianCmd:
    def test_build_points(self):
        runner = CliRunner()
        result = runner.invoke(calc, ['cartesian', '-b', '[(1,2),(3,4)]'])
        assert result.exit_code == 0
        assert '1' in result.output

    def test_total_of_sets(self):
        runner = CliRunner()
        result = runner.invoke(calc, ['cartesian', '-t', '[2, 3, 4]'])
        assert result.exit_code == 0
        assert '24' in result.output

    def test_invalid_b_input_shows_error(self):
        runner = CliRunner()
        result = runner.invoke(calc, ['cartesian', '-b', 'not_valid'])
        assert result.exit_code == 0
        assert 'Correct use' in result.output


class TestTrinomialCmd:
    def test_basic_output_contains_x1_x2(self):
        runner = CliRunner()
        result = runner.invoke(calc, ['trinomial', '1', 'n5', '6'])
        assert result.exit_code == 0
        assert 'x1' in result.output
        assert 'x2' in result.output

    def test_negative_coef_prefix(self):
        runner = CliRunner()
        result = runner.invoke(calc, ['trinomial', '1', 'n2', '1'])
        assert result.exit_code == 0
        assert 'xv' in result.output
