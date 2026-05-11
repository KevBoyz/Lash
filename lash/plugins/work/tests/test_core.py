# pytest lash/plugins/work/tests/test_core.py
import json
import pytest
from lash.plugins.work.core import (
    time_format, time_conversor, make_files,
    save_cache, load_cache, del_cache, save_session,
)


class TestTimeFormat:
    def test_single_digit_padded(self):
        assert time_format(1, 2, 3) == ['01', '02', '03']

    def test_double_digit_unchanged(self):
        assert time_format(10, 30, 59) == ['10', '30', '59']

    def test_zero_padded(self):
        assert time_format(0) == ['00']


class TestTimeConversor:
    def test_zero_seconds(self):
        real_time, minutes = time_conversor(0)
        assert real_time == '00:00:00'
        assert minutes == 0

    def test_one_minute(self):
        real_time, minutes = time_conversor(60)
        assert minutes == 1
        assert '01' in real_time

    def test_one_hour(self):
        real_time, minutes = time_conversor(3600)
        assert real_time == '01:00:00'
        assert minutes == 60

    def test_mixed_hms(self):
        real_time, minutes = time_conversor(3661)  # 1h 1m 1s
        assert real_time == '01:01:01'
        assert minutes == 61

    def test_returns_tuple(self):
        result = time_conversor(120)
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestMakeFiles:
    def test_creates_csv_if_missing(self, tmp_path):
        csv = str(tmp_path / 'work.csv')
        cache = str(tmp_path / 'cache.json')
        make_files(False, cache, csv)
        with open(csv) as f:
            header = f.read()
        assert 'date' in header
        assert 'minutes' in header
        assert 'real_time' in header
        assert 'message' in header

    def test_does_not_overwrite_existing_csv(self, tmp_path):
        csv = str(tmp_path / 'work.csv')
        cache = str(tmp_path / 'cache.json')
        with open(csv, 'w') as f:
            f.write('existing content\n')
        make_files(False, cache, csv)
        with open(csv) as f:
            assert f.read() == 'existing content\n'

    def test_creates_cache_when_s_true(self, tmp_path):
        csv = str(tmp_path / 'work.csv')
        cache = str(tmp_path / 'cache.json')
        make_files(True, cache, csv)
        assert (tmp_path / 'cache.json').exists()

    def test_does_not_create_cache_when_s_false(self, tmp_path):
        csv = str(tmp_path / 'work.csv')
        cache = str(tmp_path / 'cache.json')
        make_files(False, cache, csv)
        assert not (tmp_path / 'cache.json').exists()


class TestSaveCacheLoadCache:
    def test_roundtrip(self, tmp_path):
        cache = str(tmp_path / 'cache.json')
        data = {'year': 2024, 'month': 5, 'day': 10, 'hour': 9, 'minute': 30}
        save_cache(cache, data)
        result = load_cache(cache)
        assert result == data

    def test_save_overwrites(self, tmp_path):
        cache = str(tmp_path / 'cache.json')
        save_cache(cache, {'hour': 8})
        save_cache(cache, {'hour': 9})
        result = load_cache(cache)
        assert result == {'hour': 9}


class TestDelCache:
    def test_removes_file(self, tmp_path):
        cache = str(tmp_path / 'cache.json')
        cache_path = tmp_path / 'cache.json'
        cache_path.write_text('{}')
        del_cache(cache)
        assert not cache_path.exists()

    def test_raises_if_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            del_cache(str(tmp_path / 'nonexistent.json'))


class TestSaveSession:
    def test_appends_row(self, tmp_path):
        pytest.importorskip('pandas')
        import pandas as pd
        csv = str(tmp_path / 'work.csv')
        with open(csv, 'w') as f:
            f.write('date,minutes,real_time,message\n')
        save_session(csv, '2024-05-10', 90, '01:30:00', 'focus session')
        df = pd.read_csv(csv)
        assert len(df) == 1
        assert df.iloc[0]['minutes'] == 90
        assert df.iloc[0]['message'] == 'focus session'

    def test_preserves_existing_rows(self, tmp_path):
        pytest.importorskip('pandas')
        import pandas as pd
        csv = str(tmp_path / 'work.csv')
        with open(csv, 'w') as f:
            f.write('date,minutes,real_time,message\n')
            f.write('2024-05-09,60,01:00:00,old\n')
        save_session(csv, '2024-05-10', 30, '00:30:00', 'new')
        df = pd.read_csv(csv)
        assert len(df) == 2
        assert df.iloc[0]['message'] == 'old'
        assert df.iloc[1]['message'] == 'new'
