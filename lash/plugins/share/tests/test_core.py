# pytest lash/plugins/share/tests/test_core.py
A, B, C = "192.168.0.2", "192.168.0.3", "192.168.0.4"


def _state_with_two_files(tmp_path):
    from lash.plugins.share.core import ShareState
    state = ShareState()
    state.touch(A, "pc-a", 0.0)
    state.touch(B, "pc-b", 0.0)
    state.add_file("f1", "a.txt", 5, A, tmp_path / "f1")
    state.add_file("f2", "b.txt", 7, B, tmp_path / "f2")
    return state


class TestTouch:
    def test_retorna_true_so_na_primeira_vez(self):
        from lash.plugins.share.core import ShareState
        state = ShareState()
        assert state.touch(A, "pc-a", 0.0) is True
        assert state.touch(A, "outro", 1.0) is False
        assert state.device_name(A) == "pc-a"

    def test_aparelho_some_da_lista_apos_timeout(self):
        from lash.plugins.share.core import ShareState
        state = ShareState()
        state.touch(A, "pc-a", 0.0)
        state.touch(B, "pc-b", 10.5)
        ips = [d["ip"] for d in state.snapshot(B, 10.5)["devices"]]
        assert ips == [B]

    def test_set_name_atualiza_nome(self):
        from lash.plugins.share.core import ShareState
        state = ShareState()
        state.touch(A, "Android · Chrome", 0.0)
        state.set_name(A, "MOTO-G")
        assert state.device_name(A) == "MOTO-G"

    def test_nome_de_ip_desconhecido_e_o_ip(self):
        from lash.plugins.share.core import ShareState
        assert ShareState().device_name(C) == C


class TestClaimDownload:
    def test_primeiro_claim_retorna_arquivo_e_segundo_none(self, tmp_path):
        state = _state_with_two_files(tmp_path)
        assert state.claim_download("f1", B).id == "f1"
        assert state.claim_download("f1", B) is None

    def test_quem_enviou_nao_pode_baixar(self, tmp_path):
        state = _state_with_two_files(tmp_path)
        assert state.claim_download("f1", A) is None

    def test_id_inexistente_retorna_none(self, tmp_path):
        state = _state_with_two_files(tmp_path)
        assert state.claim_download("nope", B) is None


class TestSnapshot:
    def test_separa_disponiveis_e_meus_uploads(self, tmp_path):
        snap = _state_with_two_files(tmp_path).snapshot(A, 1.0)
        assert [f["id"] for f in snap["available"]] == ["f2"]
        assert snap["available"][0]["from"] == "pc-b"
        assert [f["id"] for f in snap["uploads"]] == ["f1"]

    def test_marca_downloaded_e_conta_downloads(self, tmp_path):
        state = _state_with_two_files(tmp_path)
        state.claim_download("f1", B)
        assert state.snapshot(B, 1.0)["available"][0]["downloaded"] is True
        assert state.snapshot(A, 1.0)["uploads"][0]["downloads"] == 1

    def test_marca_me_na_lista_de_dispositivos(self, tmp_path):
        snap = _state_with_two_files(tmp_path).snapshot(A, 1.0)
        assert (snap["me"]["ip"], snap["me"]["name"]) == (A, "pc-a")
        assert {d["ip"]: d["me"] for d in snap["devices"]} == {A: True, B: False}

    def test_arquivos_mais_recentes_primeiro(self, tmp_path):
        state = _state_with_two_files(tmp_path)
        state.add_file("f3", "c.txt", 1, B, tmp_path / "f3")
        assert [f["id"] for f in state.snapshot(A, 1.0)["available"]] == ["f3", "f2"]


class TestStorage:
    def test_reset_cria_pasta_vazia_e_apaga_restos(self, tmp_path):
        from lash.plugins.share.core import reset_storage
        folder = tmp_path / "files"
        folder.mkdir()
        (folder / "old.bin").write_bytes(b"x")
        reset_storage(folder)
        assert folder.is_dir() and list(folder.iterdir()) == []

    def test_cleanup_remove_pasta(self, tmp_path):
        from lash.plugins.share.core import cleanup_storage
        folder = tmp_path / "files"
        (folder / "sub").mkdir(parents=True)
        cleanup_storage(folder)
        assert not folder.exists()

    def test_cleanup_ignora_pasta_inexistente(self, tmp_path):
        from lash.plugins.share.core import cleanup_storage
        cleanup_storage(tmp_path / "nope")


H = "192.168.0.10"


class TestShareStateP2p:
    def _state(self):
        from lash.plugins.share.core import ShareState
        state = ShareState(host_ip=H, p2p=True)
        state.touch(H, "pc", 0.0)
        state.touch(A, "cel-a", 0.0)
        state.touch(B, "cel-b", 0.0)
        return state

    def test_snapshot_informa_modo_e_host(self):
        state = self._state()
        assert state.snapshot(H, 1.0)["mode"] == "p2p"
        assert state.snapshot(H, 1.0)["me"]["host"] is True
        assert state.snapshot(A, 1.0)["me"]["host"] is False

    def test_modo_normal_por_padrao(self):
        from lash.plugins.share.core import ShareState
        assert ShareState().snapshot(A, 0.0)["mode"] == "normal"

    def test_arquivo_relay_so_aparece_para_o_host(self):
        state = self._state()
        state.add_file("r1", "foto.jpg", 3, A, None, kind="relay")
        assert state.snapshot(B, 1.0)["available"] == []
        assert [f["id"] for f in state.snapshot(H, 1.0)["available"]] == ["r1"]
        assert [f["id"] for f in state.snapshot(A, 1.0)["uploads"]] == ["r1"]

    def test_pulls_so_aparecem_para_o_host(self):
        state = self._state()
        state.add_file("o1", "doc.pdf", 3, H, None, kind="offer", page="p1")
        state.add_pull("t1", "o1")
        assert state.snapshot(H, 1.0)["pulls"] == [{"transfer": "t1", "file": "o1"}]
        assert state.snapshot(A, 1.0)["pulls"] == []

    def test_drop_pull_retorna_false_se_inexistente(self):
        state = self._state()
        state.add_pull("t1", "o1")
        assert state.drop_pull("t1") is True
        assert state.drop_pull("t1") is False

    def test_nova_pagina_do_host_descarta_ofertas_antigas(self):
        state = self._state()
        state.set_host_page("p1")
        state.add_file("o1", "doc.pdf", 3, H, None, kind="offer", page="p1")
        state.set_host_page("p2")
        assert state.get_file("o1") is None

    def test_ofertas_somem_com_host_offline(self):
        state = self._state()
        state.add_file("o1", "doc.pdf", 3, H, None, kind="offer", page="p1")
        state.prune_offers(5.0)
        assert state.get_file("o1") is not None
        state.prune_offers(10.5)
        assert state.get_file("o1") is None

    def test_release_download_permite_baixar_de_novo(self):
        state = self._state()
        state.add_file("o1", "doc.pdf", 3, H, None, kind="offer", page="p1")
        assert state.claim_download("o1", A) is not None
        state.release_download("o1", A)
        assert state.claim_download("o1", A) is not None

    def test_remove_file_tira_arquivo_e_pulls(self):
        state = self._state()
        state.add_file("o1", "doc.pdf", 3, H, None, kind="offer", page="p1")
        state.add_pull("t1", "o1")
        state.remove_file("o1")
        assert state.get_file("o1") is None
        assert state.snapshot(H, 1.0)["pulls"] == []


class TestRelay:
    def _send_bg(self, relay, key, data, size=None, timeout=2.0):
        import io
        import threading
        result = {}
        n = len(data) if size is None else size
        t = threading.Thread(
            target=lambda: result.update(ok=relay.send(key, io.BytesIO(data), n, timeout)),
            daemon=True)
        t.start()
        return t, result

    def test_receptor_recebe_bytes_do_emissor(self):
        import io
        from lash.plugins.share.core import Relay
        relay = Relay()
        t, result = self._send_bg(relay, "k", b"hello")
        pipe = relay.receive("k", timeout=2.0)
        out = io.BytesIO()
        assert pipe.size == 5 and pipe.copy_to(out) is True
        t.join(2)
        assert out.getvalue() == b"hello" and result["ok"] is True

    def test_receptor_pode_chegar_antes_do_emissor(self):
        import io
        import threading
        from lash.plugins.share.core import Relay
        relay = Relay()
        got = {}

        def receiver():
            pipe = relay.receive("k", timeout=2.0)
            out = io.BytesIO()
            pipe.copy_to(out)
            got["data"] = out.getvalue()
        t = threading.Thread(target=receiver, daemon=True)
        t.start()
        assert relay.send("k", io.BytesIO(b"abc"), 3, timeout=2.0) is True
        t.join(2)
        assert got["data"] == b"abc"

    def test_send_sem_receptor_retorna_false(self):
        import io
        from lash.plugins.share.core import Relay
        assert Relay().send("k", io.BytesIO(b"x"), 1, timeout=0.1) is False

    def test_receive_sem_emissor_retorna_none(self):
        from lash.plugins.share.core import Relay
        assert Relay().receive("k", timeout=0.1) is None

    def test_stream_mais_curto_que_o_tamanho_retorna_false(self):
        import io
        from lash.plugins.share.core import Relay
        relay = Relay()
        t, result = self._send_bg(relay, "k", b"abc", size=10)
        pipe = relay.receive("k", timeout=2.0)
        assert pipe.copy_to(io.BytesIO()) is False
        t.join(2)
        assert result["ok"] is False

    def test_close_libera_emissor_sem_copiar(self):
        from lash.plugins.share.core import Relay
        relay = Relay()
        t, result = self._send_bg(relay, "k", b"abc")
        relay.receive("k", timeout=2.0).close()
        t.join(2)
        assert not t.is_alive() and result["ok"] is False

    def test_chaves_diferentes_nao_se_misturam(self):
        import io
        from lash.plugins.share.core import Relay
        relay = Relay()
        t, _ = self._send_bg(relay, "a", b"x")
        assert relay.receive("b", timeout=0.1) is None
        assert relay.receive("a", timeout=2.0).copy_to(io.BytesIO()) is True
        t.join(2)


class TestRenderQr:
    def test_gera_qr_em_varias_linhas_de_mesmo_tamanho(self):
        import pytest
        pytest.importorskip("qrcode")
        from lash.plugins.share.core import render_qr
        lines = render_qr("http://192.168.0.10:8765").splitlines()
        assert len(lines) >= 10
        assert len({len(line) for line in lines}) == 1
