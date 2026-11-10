# pytest lash/plugins/share/tests/test_cli.py
import pytest


class FakeServer:
    instances = []
    fail = None
    share_fail = None
    emit = None

    def __init__(self, storage, host_ip, port, **kwargs):
        if FakeServer.fail:
            raise FakeServer.fail
        self.storage = storage
        self.kwargs = kwargs
        self.url = f"http://{host_ip}:{port}"
        self.closed = False
        self.shared = []
        FakeServer.instances.append(self)

    def share_file(self, path):
        from types import SimpleNamespace
        self.shared.append(("file", path))
        return SimpleNamespace(name=path.name, size=path.stat().st_size)

    def share_folder(self, folder):
        from types import SimpleNamespace
        if FakeServer.share_fail:
            raise FakeServer.share_fail
        self.shared.append(("folder", folder))
        return SimpleNamespace(name=folder.name + ".zip", size=2048)

    def serve_forever(self):
        if FakeServer.emit is not None:
            (self.kwargs.get("on_event") or (lambda event: None))(FakeServer.emit)
        raise KeyboardInterrupt

    def close(self):
        self.closed = True


@pytest.fixture
def env(tmp_path, monkeypatch):
    from lash.plugins.share import cli
    FakeServer.instances, FakeServer.fail, FakeServer.emit = [], None, None
    FakeServer.share_fail = None
    monkeypatch.setattr(cli, "ShareServer", FakeServer)
    monkeypatch.setattr(cli, "render_qr", lambda url: "<QR>")
    monkeypatch.setattr(cli, "detect_lan_ip", lambda: "192.168.0.10")
    monkeypatch.setattr(cli, "storage_dir", lambda: tmp_path)
    monkeypatch.setattr("webbrowser.open", lambda url: None)
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

    def test_eventos_aparecem_no_terminal_com_verbose(self, env):
        from lash.plugins.share.helpers import ShareEvent
        FakeServer.emit = ShareEvent("connected", "loq", "192.168.0.3")
        assert "[+] loq (192.168.0.3) connected" in _run("-v").output
        assert "[+] loq (192.168.0.3) connected" in _run("--verbose").output

    def test_eventos_no_terminal_comecam_com_hora(self, env):
        import time
        from lash.plugins.share.helpers import ShareEvent
        at = time.mktime((2026, 11, 10, 14, 5, 0, 0, 0, -1))
        FakeServer.emit = ShareEvent("connected", "loq", "192.168.0.3", at=at)
        assert "14:05 [+] loq (192.168.0.3) connected" in _run("-v").output

    def test_eventos_ocultos_sem_verbose(self, env):
        from lash.plugins.share.helpers import ShareEvent
        FakeServer.emit = ShareEvent("connected", "loq", "192.168.0.3")
        assert "connected" not in _run().output

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

    def test_modo_normal_tambem_abre_navegador(self, env):
        opened = []
        env.setattr("webbrowser.open", opened.append)
        assert _run().exit_code == 0
        assert opened == ["http://192.168.0.10:8765"]


class TestShareDoTerminal:
    def test_files_separados_por_virgula(self, env, tmp_path):
        a = tmp_path / "a.txt"
        a.write_bytes(b"12345")
        b = tmp_path / "b.txt"
        b.write_bytes(b"x")
        result = _run("--files", f"{a}, {b}")
        assert result.exit_code == 0
        assert FakeServer.instances[0].shared == [("file", a), ("file", b)]
        assert "a.txt (5 B)" in result.output and "b.txt (1 B)" in result.output

    def test_folders_viram_zip(self, env, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        fotos = tmp_path / "fotos"
        fotos.mkdir()
        result = _run("--folders", f"{docs},{fotos}")
        assert result.exit_code == 0
        assert FakeServer.instances[0].shared == [("folder", docs), ("folder", fotos)]
        assert "docs.zip (2.0 KB)" in result.output

    def test_files_e_folders_juntos(self, env, tmp_path):
        a = tmp_path / "a.txt"
        a.write_bytes(b"x")
        docs = tmp_path / "docs"
        docs.mkdir()
        assert _run("--files", str(a), "--folders", str(docs)).exit_code == 0
        assert FakeServer.instances[0].shared == [("file", a), ("folder", docs)]

    def test_arquivo_inexistente_e_erro_sem_subir_servidor(self, env, tmp_path):
        result = _run("--files", str(tmp_path / "nope.txt"))
        assert result.exit_code == 2
        assert "file not found" in result.output
        assert FakeServer.instances == []

    def test_pasta_em_files_e_erro(self, env, tmp_path):
        assert _run("--files", str(tmp_path)).exit_code == 2

    def test_arquivo_em_folders_e_erro(self, env, tmp_path):
        a = tmp_path / "a.txt"
        a.write_bytes(b"x")
        result = _run("--folders", str(a))
        assert result.exit_code == 2
        assert "folder not found" in result.output

    def test_erro_ao_zipar_fecha_servidor_sem_traceback(self, env, tmp_path):
        FakeServer.share_fail = PermissionError(13, "Permission denied")
        result = _run("--folders", str(tmp_path))
        assert result.exit_code == 1
        assert "Could not share" in result.output
        assert "Traceback" not in result.output
        assert FakeServer.instances[0].closed is True

    def test_sem_opcoes_nao_lista_envios(self, env):
        assert "Sending to every device" not in _run().output

    def test_aviso_de_saida_nao_fala_em_apagar_arquivos_compartilhados(self, env, tmp_path):
        a = tmp_path / "a.txt"
        a.write_bytes(b"x")
        result = _run("--files", str(a))
        assert "Shared files removed" not in result.output
        assert "Temporary files removed" in result.output
