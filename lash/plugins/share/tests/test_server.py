# pytest lash/plugins/share/tests/test_server.py
import pytest

HOST = "127.0.0.5"


@pytest.fixture
def srv(tmp_path):
    import threading
    from lash.plugins.share.core import ShareServer
    events = []
    server = ShareServer(tmp_path / "files", host_ip=HOST, port=0,
                         on_event=lambda event: events.append(str(event)),
                         resolve_name=lambda ip: "pc-" + ip.rsplit(".", 1)[1])
    server.events = events
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server
    server.shutdown()
    server.close()


def _req(srv, method, path, body=None, source="127.0.0.2", headers=None):
    import http.client
    conn = http.client.HTTPConnection("127.0.0.1", srv.port, timeout=5,
                                      source_address=(source, 0))
    conn.request(method, path, body=body, headers=headers or {})
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, resp.headers, data


def _state(srv, source, page=""):
    import json
    path = "/api/state" + (f"?page={page}" if page else "")
    return json.loads(_req(srv, "GET", path, source=source)[2])


def _upload(srv, name, data, source="127.0.0.2"):
    import json
    from urllib.parse import quote
    status, _, body = _req(srv, "PUT", "/api/upload?name=" + quote(name), body=data, source=source)
    assert status == 201
    return json.loads(body)


def _wait(cond, timeout=2.0):
    import time
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.05)
    return False


class TestEstado:
    def test_registra_aparelho_e_retorna_me(self, srv):
        snap = _state(srv, "127.0.0.2")
        assert snap["me"]["ip"] == "127.0.0.2"
        assert [d["ip"] for d in snap["devices"]] == ["127.0.0.2"]

    def test_conexao_registrada_na_hora_com_nome_do_navegador(self, srv):
        _req(srv, "GET", "/api/state", headers={"User-Agent": "Android Chrome/130"})
        assert srv.events[0][6:] == "[+] Android · Chrome (127.0.0.2) connected"

    def test_nome_resolvido_depois_gera_evento_de_identificacao(self, srv):
        _req(srv, "GET", "/api/state", headers={"User-Agent": "Android Chrome/130"})
        assert _wait(lambda: srv.state.device_name("127.0.0.2") == "pc-2")
        assert _wait(lambda: "[~] Android · Chrome (127.0.0.2) identified as pc-2"
                     in [e[6:] for e in srv.events])

    def test_host_conecta_com_nome_da_maquina(self, srv):
        import socket
        _req(srv, "GET", "/api/state", source=HOST)
        assert srv.events[0][6:] == f"[+] {socket.gethostname()} ({HOST}) connected"

    def test_localhost_vira_ip_do_host(self, srv):
        assert _state(srv, "127.0.0.1")["me"]["ip"] == HOST


class TestUpload:
    def test_upload_registra_arquivo_e_grava_no_disco(self, srv):
        info = _upload(srv, "a.txt", b"hello")
        snap = _state(srv, "127.0.0.3")
        assert [(f["name"], f["size"]) for f in snap["available"]] == [("a.txt", 5)]
        assert (srv.storage / info["id"]).read_bytes() == b"hello"
        assert _wait(lambda: any("sent a.txt (5 B)" in e for e in srv.events))

    def test_upload_sem_nome_retorna_400(self, srv):
        assert _req(srv, "PUT", "/api/upload", body=b"x")[0] == 400

    def test_upload_mesmo_nome_nao_sobrescreve(self, srv):
        first = _upload(srv, "IMG_0001.jpg", b"1")
        second = _upload(srv, "IMG_0001.jpg", b"2", source="127.0.0.3")
        assert first["id"] != second["id"]
        assert _req(srv, "GET", f"/api/files/{first['id']}", source="127.0.0.4")[2] == b"1"
        assert _req(srv, "GET", f"/api/files/{second['id']}", source="127.0.0.4")[2] == b"2"

    def test_upload_interrompido_nao_deixa_arquivo(self, srv):
        import socket
        sock = socket.create_connection(("127.0.0.1", srv.port), source_address=("127.0.0.2", 0))
        sock.sendall(b"PUT /api/upload?name=x.bin HTTP/1.1\r\nHost: x\r\n"
                     b"Content-Length: 100\r\n\r\n" + b"0123456789")
        sock.close()
        assert _wait(lambda: not list(srv.storage.glob("*.part")))
        assert _state(srv, "127.0.0.3")["available"] == []


class TestDownload:
    def test_download_entrega_conteudo_e_nome(self, srv):
        info = _upload(srv, "relatório final (1).pdf", b"pdf")
        status, headers, body = _req(srv, "GET", f"/api/files/{info['id']}", source="127.0.0.3")
        assert (status, body) == (200, b"pdf")
        assert headers["Content-Disposition"] == (
            'attachment; filename="relatorio final (1).pdf"; '
            "filename*=UTF-8''relat%C3%B3rio%20final%20%281%29.pdf")

    def test_segundo_download_retorna_410(self, srv):
        info = _upload(srv, "a.txt", b"x")
        assert _req(srv, "GET", f"/api/files/{info['id']}", source="127.0.0.3")[0] == 200
        assert _req(srv, "GET", f"/api/files/{info['id']}", source="127.0.0.3")[0] == 410

    def test_quem_enviou_recebe_410(self, srv):
        info = _upload(srv, "a.txt", b"x")
        assert _req(srv, "GET", f"/api/files/{info['id']}")[0] == 410

    def test_id_desconhecido_retorna_404(self, srv):
        assert _req(srv, "GET", "/api/files/000000000000", source="127.0.0.3")[0] == 404

    def test_host_por_localhost_nao_baixa_proprio_upload(self, srv):
        info = _upload(srv, "a.txt", b"x", source="127.0.0.1")
        assert _req(srv, "GET", f"/api/files/{info['id']}", source=HOST)[0] == 410

    def test_quem_chega_depois_tambem_baixa(self, srv):
        info = _upload(srv, "a.txt", b"x")
        snap = _state(srv, "127.0.0.4")
        assert snap["available"][0]["downloaded"] is False
        assert _req(srv, "GET", f"/api/files/{info['id']}", source="127.0.0.4")[0] == 200
        assert _state(srv, "127.0.0.4")["available"][0]["downloaded"] is True
        assert _wait(lambda: any("downloaded a.txt" in e for e in srv.events))


@pytest.fixture
def p2p():
    import threading
    from lash.plugins.share.core import ShareServer
    events = []
    server = ShareServer(None, host_ip=HOST, port=0, p2p=True, relay_timeout=2.0,
                         on_event=lambda event: events.append(str(event)),
                         resolve_name=lambda ip: "pc-" + ip.rsplit(".", 1)[1])
    server.events = events
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server
    server.shutdown()
    server.close()


def _bg(fn):
    import threading
    result = {}
    t = threading.Thread(target=lambda: result.update(value=fn()), daemon=True)
    t.start()
    return t, result


class TestP2pEstado:
    def test_informa_modo_e_host(self, p2p):
        snap = _state(p2p, HOST)
        assert snap["mode"] == "p2p" and snap["me"]["host"] is True
        assert _state(p2p, "127.0.0.2")["me"]["host"] is False

    def test_modo_normal_informa_normal(self, srv):
        assert _state(srv, "127.0.0.2")["mode"] == "normal"

    def test_p2p_nao_mexe_em_pasta(self, monkeypatch):
        from lash.plugins.share import core
        calls = []
        monkeypatch.setattr(core, "reset_storage", calls.append)
        monkeypatch.setattr(core, "cleanup_storage", calls.append)
        server = core.ShareServer(None, host_ip=HOST, port=0, p2p=True)
        server.close()
        assert calls == []


class TestP2pCelularParaPc:
    def test_celular_envia_e_so_o_host_recebe(self, p2p):
        t, res = _bg(lambda: _req(p2p, "PUT", "/api/upload?name=foto.jpg", body=b"abc"))
        assert _wait(lambda: len(_state(p2p, HOST)["available"]) == 1)
        assert _state(p2p, "127.0.0.3")["available"] == []
        fid = _state(p2p, HOST)["available"][0]["id"]
        status, _, body = _req(p2p, "GET", f"/api/files/{fid}", source=HOST)
        assert (status, body) == (200, b"abc")
        t.join(3)
        assert res["value"][0] == 201

    def test_eventos_do_repasse_saem_em_ordem(self, p2p):
        t, _ = _bg(lambda: _req(p2p, "PUT", "/api/upload?name=foto.jpg", body=b"abc"))
        assert _wait(lambda: len(_state(p2p, HOST)["available"]) == 1)
        fid = _state(p2p, HOST)["available"][0]["id"]
        _req(p2p, "GET", f"/api/files/{fid}", source=HOST)
        t.join(3)

        def index(text):
            return next((i for i, e in enumerate(p2p.events) if text in e), None)
        assert _wait(lambda: index("sent foto.jpg") is not None
                     and index("downloaded foto.jpg") is not None)
        assert index("sent foto.jpg") < index("downloaded foto.jpg")

    def test_upload_do_celular_sem_host_retorna_504(self, p2p):
        assert _req(p2p, "PUT", "/api/upload?name=a.txt", body=b"x")[0] == 504
        assert _state(p2p, "127.0.0.2")["uploads"] == []

    def test_host_nao_usa_upload_no_p2p(self, p2p):
        assert _req(p2p, "PUT", "/api/upload?name=a.txt", body=b"x", source=HOST)[0] == 403


class TestP2pPcParaCelular:
    def _offer(self, server, name="doc.pdf", size=3, page="p1", source=HOST):
        return _req(server, "POST", f"/api/offer?name={name}&size={size}&page={page}",
                    source=source)

    def test_host_oferece_e_celular_baixa_do_navegador_do_host(self, p2p):
        import json
        status, _, body = self._offer(p2p)
        assert status == 201
        fid = json.loads(body)["id"]
        t, res = _bg(lambda: _req(p2p, "GET", f"/api/files/{fid}", source="127.0.0.2"))
        assert _wait(lambda: _state(p2p, HOST, page="p1")["pulls"] != [])
        tid = _state(p2p, HOST, page="p1")["pulls"][0]["transfer"]
        assert _req(p2p, "PUT", f"/api/relay/{tid}", body=b"pdf", source=HOST)[0] == 200
        t.join(3)
        assert (res["value"][0], res["value"][2]) == (200, b"pdf")

    def test_oferta_some_quando_pagina_do_host_recarrega(self, p2p):
        self._offer(p2p, page="p1")
        assert len(_state(p2p, "127.0.0.2")["available"]) == 1
        _state(p2p, HOST, page="p2")
        assert _state(p2p, "127.0.0.2")["available"] == []

    def test_download_de_oferta_sem_host_retorna_504_e_libera(self, p2p):
        import json
        fid = json.loads(self._offer(p2p)[2])["id"]
        assert _req(p2p, "GET", f"/api/files/{fid}", source="127.0.0.2")[0] == 504
        assert _state(p2p, "127.0.0.2")["available"][0]["downloaded"] is False
        assert _state(p2p, HOST, page="p1")["pulls"] == []

    def test_celular_nao_pode_oferecer(self, p2p):
        assert self._offer(p2p, source="127.0.0.2")[0] == 403

    def test_oferta_com_tamanho_invalido_retorna_400(self, p2p):
        assert self._offer(p2p, size="abc")[0] == 400

    def test_modo_normal_rejeita_oferta(self, srv):
        assert self._offer(srv)[0] == 403

    def test_relay_de_transferencia_desconhecida_retorna_404(self, p2p):
        assert _req(p2p, "PUT", "/api/relay/000000000000", body=b"x", source=HOST)[0] == 404


class TestRespostaComCorpoNaoLido:
    def test_erro_chega_ao_cliente_no_modo_normal(self, srv):
        assert _req(srv, "PUT", "/api/nope", body=b"x" * 300_000)[0] == 404

    def test_recusa_do_host_chega_ao_cliente_no_p2p(self, p2p):
        assert _req(p2p, "PUT", "/api/upload?name=a.bin", body=b"x" * 300_000,
                    source=HOST)[0] == 403

    def test_504_chega_ao_celular_quando_pc_nao_puxa(self, p2p):
        assert _req(p2p, "PUT", "/api/upload?name=a.bin", body=b"x" * 300_000)[0] == 504


class TestPorta:
    def test_porta_ocupada_levanta_oserror(self, srv, tmp_path):
        from lash.plugins.share.core import ShareServer
        with pytest.raises(OSError):
            other = ShareServer(tmp_path / "other", host_ip=HOST, port=srv.port)
            other.close()


class TestPagina:
    def test_raiz_retorna_html(self, srv):
        status, headers, body = _req(srv, "GET", "/")
        assert status == 200
        assert headers["Content-Type"].startswith("text/html")
        assert b"lash share" in body

    def test_rota_desconhecida_retorna_404(self, srv):
        assert _req(srv, "GET", "/nope")[0] == 404

    def test_pagina_tem_botoes_secoes_zip_e_nenhum_recurso_externo(self, srv):
        html = _req(srv, "GET", "/")[2].decode("utf-8")
        for text in ("send files", "send folder", "connected devices",
                     "available files", "my uploads", "/api/state",
                     "webkitdirectory", "buildZip", "0xEDB88320"):
            assert text in html
        assert 'src="http' not in html and 'href="http' not in html

    def test_pagina_tem_fluxo_p2p(self, srv):
        html = _req(srv, "GET", "/")[2].decode("utf-8")
        for text in ("/api/offer", "/api/relay/", ">p2p mode<",
                     "page=", "PC offline"):
            assert text in html

    def test_pagina_toda_em_ingles(self, srv):
        html = _req(srv, "GET", "/")[2].decode("utf-8")
        assert '<html lang="en">' in html
        for word in ("dispositivos", "arquivos", "meus", "você", "baixado", "baixando",
                     "pendente", "enviando", "enviado", "vazio", "pasta", "mantenha",
                     "tentando", "falha", "anunciado", "montando", "grande demais"):
            assert word not in html, word


def _original(tmp_path, name="nota.txt", data=b"hello"):
    path = tmp_path / name
    path.write_bytes(data)
    return path


def _docs_folder(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.txt").write_bytes(b"a")
    return folder


class TestCompartilharDoPc:
    def test_arquivo_do_pc_chega_aos_aparelhos_sem_copia(self, srv, tmp_path):
        import socket
        shared = srv.share_file(_original(tmp_path))
        snap = _state(srv, "127.0.0.2")
        assert [(f["name"], f["size"], f["from"]) for f in snap["available"]] == [
            ("nota.txt", 5, socket.gethostname())]
        assert list(srv.storage.iterdir()) == []
        assert _req(srv, "GET", f"/api/files/{shared.id}", source="127.0.0.2")[2] == b"hello"

    def test_pc_ve_em_meus_envios_e_nao_baixa(self, srv, tmp_path):
        shared = srv.share_file(_original(tmp_path))
        snap = _state(srv, HOST)
        assert snap["available"] == []
        assert [f["name"] for f in snap["uploads"]] == ["nota.txt"]
        assert _req(srv, "GET", f"/api/files/{shared.id}", source=HOST)[0] == 410

    def test_original_nao_e_apagado_ao_fechar(self, tmp_path):
        from lash.plugins.share.core import ShareServer
        original = _original(tmp_path)
        server = ShareServer(tmp_path / "files", host_ip=HOST, port=0)
        server.share_file(original)
        server.close()
        assert original.read_bytes() == b"hello"
        assert not (tmp_path / "files").exists()

    def test_arquivo_apagado_depois_retorna_404_e_some_da_lista(self, srv, tmp_path):
        original = _original(tmp_path)
        shared = srv.share_file(original)
        original.unlink()
        assert _req(srv, "GET", f"/api/files/{shared.id}", source="127.0.0.2")[0] == 404
        assert _state(srv, "127.0.0.2")["available"] == []

    def test_pasta_vira_zip_na_pasta_do_servidor(self, srv, tmp_path):
        import io
        import zipfile
        shared = srv.share_folder(_docs_folder(tmp_path))
        assert shared.name == "docs.zip"
        assert shared.path.parent == srv.storage
        body = _req(srv, "GET", f"/api/files/{shared.id}", source="127.0.0.2")[2]
        assert zipfile.ZipFile(io.BytesIO(body)).read("docs/a.txt") == b"a"

    def test_p2p_entrega_arquivo_do_pc_sem_pagina_do_host(self, p2p, tmp_path):
        shared = p2p.share_file(_original(tmp_path))
        assert [f["name"] for f in _state(p2p, "127.0.0.2")["available"]] == ["nota.txt"]
        status, _, body = _req(p2p, "GET", f"/api/files/{shared.id}", source="127.0.0.2")
        assert (status, body) == (200, b"hello")

    def test_p2p_zip_fica_em_pasta_temporaria_removida_ao_fechar(self, tmp_path):
        from lash.plugins.share.core import ShareServer
        server = ShareServer(None, host_ip=HOST, port=0, p2p=True)
        shared = server.share_folder(_docs_folder(tmp_path))
        assert shared.path.is_file()
        server.close()
        assert not shared.path.parent.exists()


class TestQrNaPagina:
    def test_rota_qr_retorna_svg(self, srv):
        pytest.importorskip("qrcode")
        status, headers, body = _req(srv, "GET", "/qr.svg")
        assert status == 200
        assert headers["Content-Type"] == "image/svg+xml"
        assert body.startswith(b"<svg")

    def test_qr_sem_biblioteca_retorna_404(self, srv, monkeypatch):
        from lash.plugins.share import core

        def missing(url):
            raise ImportError("No module named 'qrcode'")
        monkeypatch.setattr(core, "qr_svg", missing)
        assert _req(srv, "GET", "/qr.svg")[0] == 404

    def test_pagina_mostra_so_o_qr(self, srv):
        html = _req(srv, "GET", "/")[2].decode("utf-8")
        assert 'src="/qr.svg"' in html
        assert "scan to connect" not in html


@pytest.fixture
def quiet(tmp_path):
    """Server that never renames devices, so the log only has what each test does."""
    import threading
    from lash.plugins.share.core import ShareServer
    server = ShareServer(tmp_path / "files", host_ip=HOST, port=0,
                         resolve_name=lambda ip: None)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server
    server.shutdown()
    server.close()


def _logs(srv, after=None, source="127.0.0.2"):
    import json
    path = "/api/state" + ("" if after is None else f"?log={after}")
    return json.loads(_req(srv, "GET", path, source=source)[2])["logs"]


class TestLogNaPagina:
    def test_estado_traz_logs_com_hora(self, quiet):
        import re
        logs = _logs(quiet)
        assert len(logs) == 1
        assert re.match(r"^\d\d:\d\d \[\+\] Unknown · Browser \(127\.0\.0\.2\) connected$",
                        logs[0]["text"])

    def test_log_traz_so_linhas_depois_do_id(self, quiet):
        first = _logs(quiet)
        logs = _logs(quiet, after=first[-1]["id"], source="127.0.0.3")
        assert [line["text"][6:] for line in logs] == [
            "[+] Unknown · Browser (127.0.0.3) connected"]

    def test_log_invalido_traz_tudo(self, quiet):
        _logs(quiet)
        assert len(_logs(quiet, after="abc")) == 1

    def test_log_da_pagina_registra_mesmo_sem_verbose(self, tmp_path):
        import socket
        from lash.plugins.share.core import ShareServer
        server = ShareServer(tmp_path / "files", host_ip=HOST, port=0)
        server.share_file(_original(tmp_path))
        server.close()
        assert [line["text"][6:] for line in server.log.since(0)] == [
            f"[>] {socket.gethostname()} shared nota.txt (5 B)"]

    def test_pagina_tem_bloco_de_log(self, srv):
        html = _req(srv, "GET", "/")[2].decode("utf-8")
        for text in ("server log", "&log=", "typeLogs"):
            assert text in html
