# pytest lash/plugins/web/tests/test_cli.py
import pytest
from click.testing import CliRunner
from lash.plugins.web.cli import web


class TestNewsCmd:
    def test_no_flags_exits_ok(self):
        pytest.importorskip('gnews')
        runner = CliRunner()
        result = runner.invoke(web, ['news'])
        assert result.exit_code == 0


class TestWebHelp:
    def test_web_help_shows_commands(self):
        runner = CliRunner()
        result = runner.invoke(web, ['--help'])
        assert result.exit_code == 0
        assert 'gith' in result.output
        assert 'wiki' in result.output

    def test_gith_help(self):
        runner = CliRunner()
        result = runner.invoke(web, ['gith', '--help'])
        assert result.exit_code == 0
        assert 'profile' in result.output.lower() or 'github' in result.output.lower()

    def test_wiki_help(self):
        runner = CliRunner()
        result = runner.invoke(web, ['wiki', '--help'])
        assert result.exit_code == 0
        assert 'wikipedia' in result.output.lower()
