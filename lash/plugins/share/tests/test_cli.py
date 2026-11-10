# pytest lash/plugins/share/tests/test_cli.py
import pytest


class FakeServer:
    instances = []
    fail = None
    emit = None

    def __init__(self, storage, host_ip, port, **kwargs):
        if FakeServer.fail:
            raise FakeServer.fail
        self.storage = storage
        self.kwargs = kwargs
        self.url = f"http://{host_ip}:{port}"
        self.closed = False
        FakeServer.instances.append(self)

    def serve_forever(self):
        if FakeServer.emit is not None:
            self.kwargs["on_event"](FakeServer.emit)
        raise KeyboardInterrupt

    def close(self):
        self.closed = True


@pytest.fixture
def env(tmp_path, monkeypatch):
    from lash.plugins.share import cli
    FakeServer.instances, FakeServer.fail, FakeServer.emit = [], None, None
    monkeypatch.setattr(cli, "ShareServer", FakeServer)
    monkeypatch.setattr(cli, "render_qr", lambda url: "<QR>")
    monkeypatch.setattr(cli, "detect_lan_ip", lambda: "192.168.0.10")
    monkeypatch.setattr(cli, "storage_dir", lambda: tmp_path)
    return monkeypatch


def _run(*args):
    from click.testing import CliRunner
    from lash.plugins.share.cli import share
    return CliRunner().invoke(share, list(args))


class TestShareCmd:
    def test_mostra_qr_e_link_e_fecha_no_ctrl_c(self, env):
        result = _run()
        assert result.exit_code == 0
        assert result.output.index("<QR>") < result.output.index("http://192.168.0.10:8765")
        assert FakeServer.instances[0].closed is True
        assert "Server stopped" in result.output

    def test_ip_e_porta_customizados(self, env):
        result = _run("--ip", "10.0.0.7", "-p", "9000")
        assert "http://10.0.0.7:9000" in result.output

    def test_porta_ocupada_mostra_erro(self, env):
        FakeServer.fail = OSError(10048, "address already in use")
        result = _run()
        assert result.exit_code == 1
        assert "Could not start server on port 8765" in result.output
        assert "Traceback" not in result.output

    def test_avisa_quando_sem_rede(self, env):
        from lash.plugins.share import cli
        env.setattr(cli, "detect_lan_ip", lambda: "127.0.0.1")
        assert "No network found" in _run().output

    def test_eventos_aparecem_no_terminal(self, env):
        from lash.plugins.share.helpers import ShareEvent
        FakeServer.emit = ShareEvent("connected", "loq", "192.168.0.3")
        assert "[+] loq (192.168.0.3) connected" in _run().output

    def test_mostra_link_quando_qrcode_nao_instalado(self, env):
        from lash.plugins.share import cli

        def missing(url):
            raise ImportError("No module named 'qrcode'")
        env.setattr(cli, "render_qr", missing)
        result = _run()
        assert result.exit_code == 0
        assert "QR code unavailable" in result.output
        assert "http://192.168.0.10:8765" in result.output


class TestShareP2p:
    def test_p2p_abre_navegador_e_nao_usa_pasta(self, env):
        opened = []
        env.setattr("webbrowser.open", opened.append)
        result = _run("-p2p")
        assert result.exit_code == 0
        server = FakeServer.instances[0]
        assert server.storage is None and server.kwargs.get("p2p") is True
        assert opened == ["http://192.168.0.10:8765"]
        assert "Server stopped." in result.output
        assert "Shared files removed" not in result.output

    def test_aceita_traco_duplo(self, env):
        env.setattr("webbrowser.open", lambda url: None)
        assert _run("--p2p").exit_code == 0
        assert FakeServer.instances[0].kwargs.get("p2p") is True

    def test_p2p_junto_com_porta(self, env):
        env.setattr("webbrowser.open", lambda url: None)
        assert "http://192.168.0.10:9000" in _run("-p2p", "-p", "9000").output

    def test_modo_normal_nao_abre_navegador(self, env):
        opened = []
        env.setattr("webbrowser.open", opened.append)
        _run()
        assert opened == []
