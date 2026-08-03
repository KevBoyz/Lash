# pytest lash/plugins/github/tests/test_cli.py
from click.testing import CliRunner


class TestGithubHelp:
    def test_github_help(self):
        from lash.plugins.github.cli import github

        runner = CliRunner()
        result = runner.invoke(github, ["--help"])
        assert result.exit_code == 0
        assert "profile" in result.output.lower() or "github" in result.output.lower()
