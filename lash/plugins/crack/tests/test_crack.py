# pytest lash/plugins/crack/tests/test_crack.py
import pytest


class TestGetLast:
    def test_backslash_path(self):
        from lash.plugins.crack.core import get_last
        assert get_last('C:\\folder\\file.zip') == 'file.zip'

    def test_forward_slash_path(self):
        from lash.plugins.crack.core import get_last
        assert get_last('/home/user/archive.zip') == 'archive.zip'

    def test_path_with_quotes(self):
        from lash.plugins.crack.core import get_last
        assert get_last('/folder/"archive.zip"') == 'archive.zip'


class TestPathNoFile:
    def test_strips_filename_backslash(self):
        from lash.plugins.crack.core import path_no_file
        assert path_no_file('C:\\folder\\file.zip') == 'C:\\folder\\'

    def test_forward_slash(self):
        from lash.plugins.crack.core import path_no_file
        assert path_no_file('/home/user/file.zip') == '/home/user/'


class TestNext:
    def test_joins_single_char(self):
        from lash.plugins.crack.core import _next

        def _gen():
            yield ('a',)

        assert _next(_gen()) == 'a'

    def test_joins_multiple_chars(self):
        from lash.plugins.crack.core import _next

        def _gen():
            yield ('a', 'b', 'c')

        assert _next(_gen()) == 'abc'


class TestBrute:
    def test_letters_only_length_1(self):
        from lash.plugins.crack.core import brute
        from string import ascii_letters

        gen = brute(1, False, True, False, False, False)
        results = list(gen)
        # Each result is a tuple of chars joined into a string via _next;
        # brute returns tuples directly — verify they are 1-tuples of ascii letters
        assert len(results) > 0
        for item in results:
            assert len(item) == 1
            assert item[0] in ascii_letters

    def test_numbers_only_length_1(self):
        from lash.plugins.crack.core import brute
        from string import digits

        gen = brute(1, False, False, True, False, False)
        results = list(gen)
        assert len(results) > 0
        for item in results:
            assert len(item) == 1
            assert item[0] in digits

    def test_no_chars_raises_stop_iteration(self):
        from lash.plugins.crack.core import brute, _next

        # All char types disabled → choices is '' → product('', repeat=1) is empty
        # The generator exhausts immediately; _next raises StopIteration
        gen = brute(1, False, False, False, False, False)
        with pytest.raises(StopIteration):
            _next(gen)

    def test_ramp_starts_from_length_1(self):
        from lash.plugins.crack.core import brute, _next

        # ramp=True, length=3 → generator starts at repeat=1
        gen = brute(3, True, True, False, False, False)
        first = _next(gen)
        assert len(first) == 1

    def test_no_ramp_starts_from_max_length(self):
        from lash.plugins.crack.core import brute

        # ramp=False, length=2 → range(2, 3) → only repeat=2
        gen = brute(2, False, True, False, False, False)
        results = list(gen)
        assert len(results) > 0
        for item in results:
            assert len(item) == 2

    def test_symbols_only_length_1(self):
        from lash.plugins.crack.core import brute
        from string import punctuation

        gen = brute(1, False, False, False, True, False)
        results = list(gen)
        assert len(results) > 0
        for item in results:
            assert item[0] in punctuation

    def test_ramp_covers_all_lengths_up_to_max(self):
        from lash.plugins.crack.core import brute

        # ramp=True, length=3 → lengths 1, 2, 3 all appear
        gen = brute(3, True, False, True, False, False)
        results = list(gen)
        lengths = {len(t) for t in results}
        assert 1 in lengths
        assert 2 in lengths
        assert 3 in lengths


class TestAzipCommand:
    @pytest.mark.skip(reason=(
        "Creating password-protected ZIPs requires 'pyzipper' (not in stdlib). "
        "Install pyzipper to enable these tests."
    ))
    def test_cracks_simple_password(self, tmp_path):
        # Requires pyzipper to write encrypted ZIPs.
        # If pyzipper is available, remove the skip and use the helper below.
        pyzipper = pytest.importorskip('pyzipper')
        import os
        from click.testing import CliRunner
        from lash.plugins.crack.cli import azip

        zip_path = tmp_path / 'secret.zip'
        with pyzipper.AESZipFile(
            str(zip_path), 'w',
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zf:
            zf.setpassword(b'a')
            zf.writestr('hello.txt', 'hello world')

        runner = CliRunner()
        # -ln 3: max length 3; default -l enables letters; -n omitted so numbers disabled
        result = runner.invoke(azip, [str(zip_path), '-ln', '3'])
        assert result.exit_code == 0
        assert 'Password is: a' in result.output

    @pytest.mark.skip(reason=(
        "Creating password-protected ZIPs requires 'pyzipper' (not in stdlib). "
        "Install pyzipper to enable these tests."
    ))
    def test_password_not_found(self, tmp_path):
        # Requires pyzipper to write encrypted ZIPs.
        pyzipper = pytest.importorskip('pyzipper')
        from click.testing import CliRunner
        from lash.plugins.crack.cli import azip

        zip_path = tmp_path / 'hard.zip'
        with pyzipper.AESZipFile(
            str(zip_path), 'w',
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zf:
            zf.setpassword(b'zzz')
            zf.writestr('data.txt', 'secret')

        runner = CliRunner()
        # -ln 1: max length 1 → can never reach 'zzz' → exhausts
        result = runner.invoke(azip, [str(zip_path), '-ln', '1'])
        assert result.exit_code == 0
        assert 'Password not found' in result.output
