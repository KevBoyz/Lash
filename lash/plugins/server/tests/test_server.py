# pytest lash/plugins/server/tests/test_server.py
import os
import pytest


class TestPortVerify:
    def test_valid_port(self):
        from lash.plugins.server.core import port_verify
        assert port_verify("8080") == 8080

    def test_valid_port_returns_int(self):
        from lash.plugins.server.core import port_verify
        result = port_verify("4254")
        assert isinstance(result, int)

    def test_invalid_port_exits(self):
        from lash.plugins.server.core import port_verify
        with pytest.raises(SystemExit):
            port_verify("notaport")

    def test_invalid_port_float_string_exits(self):
        from lash.plugins.server.core import port_verify
        with pytest.raises(SystemExit):
            port_verify("80.5")


class TestInjectionClientMsg:
    def test_returns_table(self):
        from lash.plugins.server.core import injection_client_msg
        from rich.table import Table
        result = injection_client_msg()
        assert isinstance(result, Table)

    def test_table_has_rows(self):
        from lash.plugins.server.core import injection_client_msg
        result = injection_client_msg()
        assert result.row_count > 0

    def test_table_has_two_columns(self):
        from lash.plugins.server.core import injection_client_msg
        result = injection_client_msg()
        assert len(result.columns) == 2

    def test_table_contains_chdir_row(self):
        from lash.plugins.server.core import injection_client_msg
        from io import StringIO
        from rich.console import Console
        result = injection_client_msg()
        buf = StringIO()
        console = Console(file=buf, highlight=False)
        console.print(result)
        assert '-chdir' in buf.getvalue()

    def test_table_contains_kill_row(self):
        from lash.plugins.server.core import injection_client_msg
        from io import StringIO
        from rich.console import Console
        result = injection_client_msg()
        buf = StringIO()
        console = Console(file=buf, highlight=False)
        console.print(result)
        assert '-kill' in buf.getvalue()


class TestServerCommands:
    @pytest.mark.skip(reason=(
        "injection command opens real network sockets and blocks in an infinite loop — "
        "not testable without live socket infrastructure."
    ))
    def test_injection_command_skipped(self):
        pass
