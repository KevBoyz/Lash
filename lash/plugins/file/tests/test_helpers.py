# pytest lash/plugins/file/tests/test_helpers.py
from lash.plugins.file.helpers import bar_template, get_ext, get_last, file_types


class TestBarTemplate:
    def test_returns_string(self):
        assert isinstance(bar_template(), str)


class TestGetExt:
    def test_extracts_extension_lowercase(self):
        assert get_ext('photo.JPG') == '.jpg'

    def test_dot_file_returns_full(self):
        assert get_ext('.pdf') == '.pdf'

    def test_no_extension(self):
        result = get_ext('readme')
        assert isinstance(result, str)

    def test_plain_extension(self):
        assert get_ext('archive.zip') == '.zip'


class TestGetLast:
    def test_windows_path(self):
        assert get_last('C:\\Users\\foo\\file.txt') == 'file.txt'

    def test_unix_path(self):
        assert get_last('/home/user/file.txt') == 'file.txt'

    def test_filename_only(self):
        assert get_last('file.txt') == 'file.txt'


class TestFileTypes:
    def test_returns_dict_with_midia_and_docs(self):
        result = file_types()
        assert 'midia' in result
        assert 'docs' in result

    def test_images_includes_png(self):
        assert '.png' in file_types()['midia']['images']

    def test_docs_includes_pdf(self):
        assert '.pdf' in file_types()['docs']
