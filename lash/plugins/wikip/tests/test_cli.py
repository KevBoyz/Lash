# pytest lash/plugins/wikip/tests/test_cli.py
from click.testing import CliRunner


class TestWikipHelp:
    def test_wikip_help(self):
        from lash.plugins.wikip.cli import wikip

        runner = CliRunner()
        result = runner.invoke(wikip, ["--help"])
        assert result.exit_code == 0
        assert "wikipedia" in result.output.lower()
