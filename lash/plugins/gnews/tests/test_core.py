# pytest lash/plugins/gnews/tests/test_core.py


class TestFormatNews:
    def test_lista_vazia_retorna_so_quebra_de_linha(self):
        from lash.plugins.gnews.core import format_news

        assert format_news([]) == "\n"

    def test_item_vira_link_com_titulo(self):
        from lash.plugins.gnews.core import format_news

        text = format_news([{"url": "http://example.com", "title": "Test News"}])

        assert text == "\n[link=http://example.com]:magnet:[/link] Test News\n\n"

    def test_um_bloco_por_noticia_na_ordem(self):
        from lash.plugins.gnews.core import format_news

        text = format_news([
            {"url": "http://a.com", "title": "First"},
            {"url": "http://b.com", "title": "Second"},
        ])

        assert text.index("First") < text.index("Second")
        assert text.count("[link=") == 2
