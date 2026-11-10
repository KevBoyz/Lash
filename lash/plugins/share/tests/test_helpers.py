# pytest lash/plugins/share/tests/test_helpers.py
ANDROID = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36")
IPHONE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
          "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
EDGE = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 Edg/130.0")
FIREFOX_LINUX = "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0"


class TestDeviceNameFromUa:
    def test_identifica_android_chrome(self):
        from lash.plugins.share.helpers import device_name_from_ua
        assert device_name_from_ua(ANDROID) == "Android · Chrome"

    def test_identifica_iphone_safari(self):
        from lash.plugins.share.helpers import device_name_from_ua
        assert device_name_from_ua(IPHONE) == "iPhone · Safari"

    def test_identifica_windows_edge(self):
        from lash.plugins.share.helpers import device_name_from_ua
        assert device_name_from_ua(EDGE) == "Windows · Edge"

    def test_identifica_firefox_no_linux(self):
        from lash.plugins.share.helpers import device_name_from_ua
        assert device_name_from_ua(FIREFOX_LINUX) == "Linux · Firefox"

    def test_retorna_desconhecido_quando_ua_vazio(self):
        from lash.plugins.share.helpers import device_name_from_ua
        assert device_name_from_ua("") == "Unknown · Browser"


class TestResolveHostname:
    def test_retorna_primeiro_rotulo_do_nome(self, monkeypatch):
        from lash.plugins.share.helpers import resolve_hostname
        monkeypatch.setattr("socket.gethostbyaddr",
                            lambda ip: ("DESKTOP-ABC.home", [], [ip]))
        assert resolve_hostname("192.168.0.5") == "DESKTOP-ABC"

    def test_retorna_none_quando_dns_falha(self, monkeypatch):
        import socket
        from lash.plugins.share.helpers import resolve_hostname

        def fail(ip):
            raise socket.herror("not found")
        monkeypatch.setattr("socket.gethostbyaddr", fail)
        assert resolve_hostname("192.168.0.5") is None

    def test_retorna_none_quando_nome_igual_ao_ip(self, monkeypatch):
        from lash.plugins.share.helpers import resolve_hostname
        monkeypatch.setattr("socket.gethostbyaddr", lambda ip: (ip, [], [ip]))
        assert resolve_hostname("192.168.0.5") is None


class _FakeUdp:
    def __init__(self, *args, fail=False):
        self.fail = fail

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def connect(self, addr):
        if self.fail:
            raise OSError("network unreachable")

    def getsockname(self):
        return ("192.168.0.10", 50000)


class TestDetectLanIp:
    def test_retorna_ip_do_socket_udp(self, monkeypatch):
        from lash.plugins.share.helpers import detect_lan_ip
        monkeypatch.setattr("socket.socket", lambda *a: _FakeUdp())
        assert detect_lan_ip() == "192.168.0.10"

    def test_retorna_loopback_quando_sem_rede(self, monkeypatch):
        from lash.plugins.share.helpers import detect_lan_ip
        monkeypatch.setattr("socket.socket", lambda *a: _FakeUdp(fail=True))
        assert detect_lan_ip() == "127.0.0.1"


class TestSafeFilename:
    def test_remove_caminho(self):
        from lash.plugins.share.helpers import safe_filename
        assert safe_filename("../../etc/passwd") == "passwd"
        assert safe_filename("C:\\dir\\a.txt") == "a.txt"

    def test_troca_caracteres_proibidos(self):
        from lash.plugins.share.helpers import safe_filename
        assert safe_filename('a<b>:c?.txt') == "a_b__c_.txt"

    def test_mantem_acentos_e_espacos(self):
        from lash.plugins.share.helpers import safe_filename
        assert safe_filename("relatório final (1).pdf") == "relatório final (1).pdf"

    def test_nome_vazio_vira_file(self):
        from lash.plugins.share.helpers import safe_filename
        assert safe_filename("") == "file"
        assert safe_filename("..") == "file"

    def test_remove_pontos_e_espacos_finais(self):
        from lash.plugins.share.helpers import safe_filename
        assert safe_filename("nome. ") == "nome"


class TestFormatSize:
    def test_formata_unidades(self):
        from lash.plugins.share.helpers import format_size
        assert format_size(0) == "0 B"
        assert format_size(1023) == "1023 B"
        assert format_size(1536) == "1.5 KB"
        assert format_size(5 * 1024 ** 3) == "5.0 GB"


def _at(hour, minute):
    import time
    return time.mktime((2026, 11, 10, hour, minute, 30, 0, 0, -1))


class TestShareEvent:
    def test_texto_de_cada_tipo(self):
        from lash.plugins.share.helpers import ShareEvent
        at = _at(14, 5)
        assert str(ShareEvent("connected", "loq", "192.168.0.3", at=at)) == \
            "14:05 [+] loq (192.168.0.3) connected"
        assert str(ShareEvent("renamed", "MOTO-G", "192.168.0.2", previous="Android · Chrome",
                              at=at)) == \
            "14:05 [~] Android · Chrome (192.168.0.2) identified as MOTO-G"
        assert str(ShareEvent("sent", "MOTO-G", "192.168.0.2", file="a.txt", size=5, at=at)) == \
            "14:05 [>] MOTO-G sent a.txt (5 B)"
        assert str(ShareEvent("shared", "loq", "192.168.0.3", file="a.txt", size=1536, at=at)) == \
            "14:05 [>] loq shared a.txt (1.5 KB)"
        assert str(ShareEvent("downloaded", "loq", "192.168.0.3", file="a.txt", at=at)) == \
            "14:05 [<] loq downloaded a.txt"

    def test_hora_com_dois_digitos_e_24h(self):
        from lash.plugins.share.helpers import ShareEvent
        assert str(ShareEvent("connected", "loq", "1.2.3.4", at=_at(9, 7))).startswith("09:07 ")
        assert str(ShareEvent("connected", "loq", "1.2.3.4", at=_at(23, 59))).startswith("23:59 ")

    def test_hora_padrao_e_o_momento_do_evento(self):
        import re
        from lash.plugins.share.helpers import ShareEvent
        assert re.match(r"^\d\d:\d\d \[\+\] ", str(ShareEvent("connected", "loq", "1.2.3.4")))


class TestFormatEvent:
    def test_texto_colorido_tem_o_mesmo_conteudo(self):
        from lash.plugins.share.helpers import ShareEvent, format_event
        event = ShareEvent("sent", "MOTO-G", "192.168.0.2", file="[a].txt", size=5)
        text = format_event(event)
        assert text.plain == str(event)
        assert text.spans

    def test_cada_tipo_tem_cor_propria(self):
        from lash.plugins.share.helpers import ShareEvent, format_event
        kinds = ("connected", "renamed", "sent", "shared", "downloaded")
        styles = {str(format_event(ShareEvent(k, "x", "1.2.3.4", file="f", previous="y")).spans[0].style)
                  for k in kinds}
        assert len(styles) == len(kinds)


class TestContentDisposition:
    def test_codifica_utf8_e_gera_fallback_ascii(self):
        from lash.plugins.share.helpers import content_disposition
        assert content_disposition("relatório final (1).pdf") == (
            'attachment; filename="relatorio final (1).pdf"; '
            "filename*=UTF-8''relat%C3%B3rio%20final%20%281%29.pdf")

    def test_troca_aspas_no_fallback(self):
        from lash.plugins.share.helpers import content_disposition
        assert content_disposition('a"b.txt').startswith('attachment; filename="a_b.txt"')


class TestSplitPaths:
    def test_separa_por_virgula_e_tira_espacos(self):
        from pathlib import Path
        from lash.plugins.share.helpers import split_paths
        assert split_paths(["a.txt, b/c.pdf"]) == [Path("a.txt"), Path("b/c.pdf")]

    def test_junta_opcao_repetida_e_ignora_vazios_e_repetidos(self):
        from pathlib import Path
        from lash.plugins.share.helpers import split_paths
        assert split_paths(["a.txt,,", "b.txt, a.txt"]) == [Path("a.txt"), Path("b.txt")]

    def test_expande_til(self):
        from pathlib import Path
        from lash.plugins.share.helpers import split_paths
        assert split_paths(["~/x.txt"]) == [Path.home() / "x.txt"]

    def test_sem_valores_retorna_lista_vazia(self):
        from lash.plugins.share.helpers import split_paths
        assert split_paths(()) == []
