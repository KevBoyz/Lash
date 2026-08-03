# pytest lash/plugins/gnews/tests/test_cli.py
import pytest
from click.testing import CliRunner


class TestGnewsCmd:
    def test_no_flags_exits_ok(self):
        pytest.importorskip("gnews")
        from lash.plugins.gnews.cli import gnews

        runner = CliRunner()
        result = runner.invoke(gnews, [])
        assert result.exit_code == 0
