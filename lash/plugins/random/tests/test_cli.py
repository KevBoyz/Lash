# pytest lash/plugins/random/tests/test_cli.py
from click.testing import CliRunner
from lash.plugins.random.cli import random


class TestRandomCli:
    def test_default_outputs_5_chars(self):
        runner = CliRunner()
        result = runner.invoke(random, [])
        assert result.exit_code == 0
        output = result.output.strip()
        assert len(output) == 5

    def test_c_flag_controls_length(self):
        runner = CliRunner()
        result = runner.invoke(random, ['-c', '10'])
        assert result.exit_code == 0
        assert len(result.output.strip()) == 10

    def test_l_flag_produces_letters(self):
        runner = CliRunner()
        result = runner.invoke(random, ['-c', '20', '-l'])
        assert result.exit_code == 0

    def test_s_flag_produces_symbols(self):
        runner = CliRunner()
        result = runner.invoke(random, ['-c', '10', '-s'])
        assert result.exit_code == 0

    def test_f_flag_saves_file(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(random, ['-c', '5', '-f'])
            assert result.exit_code == 0
            assert 'Saved to' in result.output
