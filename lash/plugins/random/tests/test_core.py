# pytest lash/plugins/random/tests/test_core.py
import os
import pytest
from lash.plugins.random.core import get_size, gen_random, file_save


class TestGetSize:
    def test_numbers_only(self):
        assert get_size(10, True, False, False) == 10

    def test_numbers_and_letters(self):
        assert get_size(10, True, False, True) == 5

    def test_all_three_sets(self):
        assert get_size(9, True, True, True) == 3

    def test_no_sets_returns_c(self):
        assert get_size(8, False, False, False) == 8

    def test_letters_only(self):
        assert get_size(6, False, True, False) == 6


class TestGenRandom:
    def test_numbers_only_all_digits(self):
        result = gen_random(20, n=True, s=False, l=False, ul=False)
        assert all(c.isdigit() for c in result)

    def test_letters_only_all_alpha(self):
        result = gen_random(20, n=False, s=False, l=True, ul=False)
        assert all(c.isalpha() for c in result)

    def test_symbols_only_all_symbols(self):
        symbols = set('!?@#$%&*_+-')
        result = gen_random(20, n=False, s=True, l=False, ul=False)
        assert all(c in symbols for c in result)

    def test_numbers_and_letters_length(self):
        result = gen_random(5, n=True, s=False, l=True, ul=False)
        assert len(result) == 10  # 2 chars per iteration (n + l)

    def test_returns_list(self):
        result = gen_random(3, n=True, s=False, l=False, ul=False)
        assert isinstance(result, list)

    def test_empty_size_returns_empty(self):
        result = gen_random(0, n=True, s=False, l=False, ul=False)
        assert result == []

    def test_ul_flag_produces_mixed_case(self):
        result = gen_random(100, n=False, s=False, l=True, ul=True)
        joined = ''.join(result)
        assert any(c.isupper() for c in joined) or any(c.islower() for c in joined)


class TestFileSave:
    def test_creates_file(self, tmp_path):
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            fname = file_save(['a', 'b', 'c'])
            assert os.path.exists(fname)
        finally:
            os.chdir(original_dir)

    def test_returns_filename(self, tmp_path):
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            fname = file_save(['x', 'y', 'z'])
            assert fname.startswith('output') and fname.endswith('.txt')
        finally:
            os.chdir(original_dir)

    def test_file_content_matches(self, tmp_path):
        original_dir = os.getcwd()
        os.chdir(tmp_path)
        try:
            fname = file_save(['h', 'e', 'l', 'l', 'o'])
            with open(fname) as f:
                assert f.read() == 'hello'
        finally:
            os.chdir(original_dir)
