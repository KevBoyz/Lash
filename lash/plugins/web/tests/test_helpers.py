# pytest lash/plugins/web/tests/test_helpers.py
from lash.plugins.web.helpers import impress_news


class TestImpressNews:
    def test_empty_list_no_crash(self):
        impress_news([])

    def test_single_item_no_crash(self):
        impress_news([{'url': 'http://example.com', 'title': 'Test News'}])
