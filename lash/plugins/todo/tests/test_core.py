# pytest lash/plugins/todo/tests/test_core.py
from datetime import date, timedelta


class TestAddTask:
    def test_add_creates_task(self):
        from lash.plugins.todo.core import add_task
        state = {"tasks": [], "active": None}
        task = add_task(state, "write report")
        assert task["name"] == "write report"
        assert not task["done"]
        assert state["tasks"] == [task]

    def test_duplicate_pending_raises(self):
        from lash.plugins.todo.core import add_task
        import pytest
        state = {"tasks": [], "active": None}
        add_task(state, "deploy")
        with pytest.raises(ValueError):
            add_task(state, "deploy")


class TestRemoveTask:
    def test_remove_by_name(self):
        from lash.plugins.todo.core import add_task, remove_task
        state = {"tasks": [], "active": None}
        add_task(state, "foo")
        removed = remove_task(state, "foo")
        assert removed["name"] == "foo"
        assert state["tasks"] == []

    def test_cannot_remove_active(self):
        from lash.plugins.todo.core import add_task, start_task, remove_task
        import pytest
        state = {"tasks": [], "active": None}
        t = add_task(state, "foo")
        start_task(state, t["id"])
        with pytest.raises(ValueError):
            remove_task(state, "foo")


class TestStartStop:
    def test_start_then_complete_creates_session_entry(self):
        from lash.plugins.todo.core import add_task, start_task, stop_task
        state = {"tasks": [], "active": None}
        t = add_task(state, "task-x")
        start_task(state, t["id"])
        entry = stop_task(state, done=True)
        assert entry is not None
        assert entry["task_name"] == "task-x"
        assert entry["done"] is True
        assert state["active"] is None
        assert t["done"] is True

    def test_pause_resumes(self):
        from lash.plugins.todo.core import add_task, start_task, pause_task
        state = {"tasks": [], "active": None}
        t = add_task(state, "task-y")
        start_task(state, t["id"])
        assert pause_task(state) == "paused"
        assert pause_task(state) == "resumed"


class TestSevenDayTotals:
    def test_buckets_last_7_days(self):
        from lash.plugins.todo.core import seven_day_totals
        today = date(2026, 10, 2)
        sessions = [
            {"date": today.isoformat(), "total_minutes": 30, "task_name": "a",
             "pomo_sessions": 0},
            {"date": (today - timedelta(days=1)).isoformat(),
             "total_minutes": 60, "task_name": "b", "pomo_sessions": 0},
            {"date": (today - timedelta(days=10)).isoformat(),
             "total_minutes": 99, "task_name": "old", "pomo_sessions": 0},
        ]
        totals = seven_day_totals(sessions, today=today)
        assert len(totals) == 7
        assert totals[-1]["date"] == today
        assert totals[-1]["minutes"] == 30
        assert totals[-2]["minutes"] == 60
        assert all(t["minutes"] >= 0 for t in totals)
        assert sum(t["minutes"] for t in totals) == 90


class TestFormatDuration:
    def test_minutes_only(self):
        from lash.plugins.todo.helpers import format_duration
        assert format_duration(125) == "2m 05s"

    def test_hours(self):
        from lash.plugins.todo.helpers import format_duration
        assert format_duration(3661) == "1h 01m 01s"

    def test_seconds_only(self):
        from lash.plugins.todo.helpers import format_duration
        assert format_duration(42) == "42s"


class TestFormatMinutesShort:
    def test_minutes(self):
        from lash.plugins.todo.helpers import format_minutes_short
        assert format_minutes_short(45) == "45min"

    def test_hours_minutes(self):
        from lash.plugins.todo.helpers import format_minutes_short
        assert format_minutes_short(135) == "2h15min"

    def test_hours_only(self):
        from lash.plugins.todo.helpers import format_minutes_short
        assert format_minutes_short(120) == "2h"

    def test_zero(self):
        from lash.plugins.todo.helpers import format_minutes_short
        assert format_minutes_short(0) == "0min"


class TestDataDir:
    def test_data_dir_uses_todo_subdir(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        from lash.plugins.todo.helpers import data_dir
        d = data_dir()
        assert d == tmp_path / ".lash" / "data" / "todo"
        assert d.exists()
