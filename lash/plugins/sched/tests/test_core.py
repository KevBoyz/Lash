# pytest lash/plugins/sched/tests/test_core.py
from lash.plugins.sched.core import reg_crono, time_format


class TestRegCrono:
    def test_decrements_seconds(self):
        assert reg_crono(0, 0, 10) == (0, 0, 9)

    def test_seconds_zero_borrows_from_minutes(self):
        h, m, s = reg_crono(0, 1, 0)
        assert (h, m, s) == (0, 0, 59)

    def test_minutes_zero_borrows_from_hours(self):
        h, m, s = reg_crono(1, 0, 0)
        assert (h, m, s) == (0, 59, 0)

    def test_all_zero_unchanged(self):
        assert reg_crono(0, 0, 0) == (0, 0, 0)

    def test_one_second_countdown(self):
        assert reg_crono(0, 0, 1) == (0, 0, 0)

    def test_one_minute_countdown_sequence(self):
        h, m, s = 0, 1, 0
        h, m, s = reg_crono(h, m, s)
        assert (h, m, s) == (0, 0, 59)
        h, m, s = reg_crono(h, m, s)
        assert (h, m, s) == (0, 0, 58)

    def test_full_hour_borrow_chain(self):
        h, m, s = reg_crono(1, 0, 0)
        assert h == 0
        assert m == 59
        assert s == 0

    def test_no_off_by_one_at_minute_boundary(self):
        # After borrowing from a minute, next decrement should give s=58, not 59 again
        h, m, s = reg_crono(0, 1, 0)   # → 0:0:59
        h, m, s = reg_crono(h, m, s)   # → 0:0:58
        assert s == 58


class TestTimeFormat:
    def test_single_digit_padded(self):
        assert time_format(1, 2, 3) == ['01', '02', '03']

    def test_double_digit_unchanged(self):
        assert time_format(10, 30, 59) == ['10', '30', '59']

    def test_zero_padded(self):
        assert time_format(0) == ['00']

    def test_mixed(self):
        assert time_format(1, 10) == ['01', '10']

    def test_returns_list(self):
        result = time_format(5, 5, 5)
        assert isinstance(result, list)
        assert len(result) == 3
