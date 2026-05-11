# pytest lash/plugins/monitor/tests/test_monitor.py


class TestGetListOfProcessSortedByMemory:
    def test_returns_list_sorted_by_vms_descending(self):
        from unittest.mock import MagicMock, patch
        import psutil as ps
        from lash.plugins.monitor.core import getListOfProcessSortedByMemory

        def make_proc(pid, name, username, vms_bytes):
            proc = MagicMock()
            proc.as_dict.return_value = {'pid': pid, 'name': name, 'username': username}
            proc.memory_info.return_value.vms = vms_bytes
            return proc

        procs = [
            make_proc(1, 'low_mem',  'user', 50  * 1024 * 1024),
            make_proc(2, 'high_mem', 'user', 200 * 1024 * 1024),
            make_proc(3, 'mid_mem',  'user', 100 * 1024 * 1024),
        ]

        with patch('lash.plugins.monitor.core.ps.process_iter', return_value=procs):
            result = getListOfProcessSortedByMemory()

        assert result[0]['name'] == 'high_mem'
        assert result[1]['name'] == 'mid_mem'
        assert result[2]['name'] == 'low_mem'

    def test_vms_converted_from_bytes_to_mb(self):
        from unittest.mock import MagicMock, patch
        from lash.plugins.monitor.core import getListOfProcessSortedByMemory
        import pytest

        proc = MagicMock()
        proc.as_dict.return_value = {'pid': 42, 'name': 'testproc', 'username': 'alice'}
        proc.memory_info.return_value.vms = 256 * 1024 * 1024  # 256 MB in bytes

        with patch('lash.plugins.monitor.core.ps.process_iter', return_value=[proc]):
            result = getListOfProcessSortedByMemory()

        assert result[0]['vms'] == pytest.approx(256.0)

    def test_result_dicts_contain_required_keys(self):
        from unittest.mock import MagicMock, patch
        from lash.plugins.monitor.core import getListOfProcessSortedByMemory

        proc = MagicMock()
        proc.as_dict.return_value = {'pid': 7, 'name': 'myproc', 'username': 'bob'}
        proc.memory_info.return_value.vms = 10 * 1024 * 1024

        with patch('lash.plugins.monitor.core.ps.process_iter', return_value=[proc]):
            result = getListOfProcessSortedByMemory()

        assert len(result) == 1
        entry = result[0]
        assert 'pid'      in entry
        assert 'name'     in entry
        assert 'username' in entry
        assert 'vms'      in entry

    def test_returns_empty_list_when_no_processes(self):
        from unittest.mock import patch
        from lash.plugins.monitor.core import getListOfProcessSortedByMemory

        with patch('lash.plugins.monitor.core.ps.process_iter', return_value=[]):
            result = getListOfProcessSortedByMemory()

        assert result == []

    def test_skips_process_that_raises_no_such_process(self):
        from unittest.mock import MagicMock, patch
        import psutil as ps
        from lash.plugins.monitor.core import getListOfProcessSortedByMemory

        bad_proc = MagicMock()
        bad_proc.as_dict.side_effect = ps.NoSuchProcess(pid=99)

        good_proc = MagicMock()
        good_proc.as_dict.return_value = {'pid': 1, 'name': 'good', 'username': 'user'}
        good_proc.memory_info.return_value.vms = 8 * 1024 * 1024

        with patch('lash.plugins.monitor.core.ps.process_iter', return_value=[bad_proc, good_proc]):
            result = getListOfProcessSortedByMemory()

        assert len(result) == 1
        assert result[0]['name'] == 'good'

    def test_skips_process_that_raises_access_denied(self):
        from unittest.mock import MagicMock, patch
        import psutil as ps
        from lash.plugins.monitor.core import getListOfProcessSortedByMemory

        bad_proc = MagicMock()
        bad_proc.as_dict.side_effect = ps.AccessDenied(pid=55)

        good_proc = MagicMock()
        good_proc.as_dict.return_value = {'pid': 2, 'name': 'allowed', 'username': 'user'}
        good_proc.memory_info.return_value.vms = 4 * 1024 * 1024

        with patch('lash.plugins.monitor.core.ps.process_iter', return_value=[bad_proc, good_proc]):
            result = getListOfProcessSortedByMemory()

        assert len(result) == 1
        assert result[0]['name'] == 'allowed'

    def test_skips_process_that_raises_zombie_process(self):
        from unittest.mock import MagicMock, patch
        import psutil as ps
        from lash.plugins.monitor.core import getListOfProcessSortedByMemory

        bad_proc = MagicMock()
        bad_proc.as_dict.side_effect = ps.ZombieProcess(pid=77)

        good_proc = MagicMock()
        good_proc.as_dict.return_value = {'pid': 3, 'name': 'alive', 'username': 'user'}
        good_proc.memory_info.return_value.vms = 16 * 1024 * 1024

        with patch('lash.plugins.monitor.core.ps.process_iter', return_value=[bad_proc, good_proc]):
            result = getListOfProcessSortedByMemory()

        assert len(result) == 1
        assert result[0]['name'] == 'alive'

    def test_all_bad_processes_returns_empty(self):
        from unittest.mock import MagicMock, patch
        import psutil as ps
        from lash.plugins.monitor.core import getListOfProcessSortedByMemory

        p1 = MagicMock()
        p1.as_dict.side_effect = ps.NoSuchProcess(pid=1)
        p2 = MagicMock()
        p2.as_dict.side_effect = ps.AccessDenied(pid=2)
        p3 = MagicMock()
        p3.as_dict.side_effect = ps.ZombieProcess(pid=3)

        with patch('lash.plugins.monitor.core.ps.process_iter', return_value=[p1, p2, p3]):
            result = getListOfProcessSortedByMemory()

        assert result == []

    def test_single_process_returns_single_entry(self):
        from unittest.mock import MagicMock, patch
        from lash.plugins.monitor.core import getListOfProcessSortedByMemory
        import pytest

        proc = MagicMock()
        proc.as_dict.return_value = {'pid': 10, 'name': 'solo', 'username': 'root'}
        proc.memory_info.return_value.vms = 1024 * 1024  # 1 MB

        with patch('lash.plugins.monitor.core.ps.process_iter', return_value=[proc]):
            result = getListOfProcessSortedByMemory()

        assert len(result) == 1
        assert result[0]['pid'] == 10
        assert result[0]['name'] == 'solo'
        assert result[0]['username'] == 'root'
        assert result[0]['vms'] == pytest.approx(1.0)

    def test_equal_vms_processes_all_present(self):
        from unittest.mock import MagicMock, patch
        from lash.plugins.monitor.core import getListOfProcessSortedByMemory

        def make_proc(pid, name):
            proc = MagicMock()
            proc.as_dict.return_value = {'pid': pid, 'name': name, 'username': 'user'}
            proc.memory_info.return_value.vms = 64 * 1024 * 1024
            return proc

        procs = [make_proc(1, 'alpha'), make_proc(2, 'beta'), make_proc(3, 'gamma')]

        with patch('lash.plugins.monitor.core.ps.process_iter', return_value=procs):
            result = getListOfProcessSortedByMemory()

        assert len(result) == 3
        names = {r['name'] for r in result}
        assert names == {'alpha', 'beta', 'gamma'}

    def test_zero_vms_process_sorts_last(self):
        from unittest.mock import MagicMock, patch
        from lash.plugins.monitor.core import getListOfProcessSortedByMemory
        import pytest

        def make_proc(pid, name, vms_bytes):
            proc = MagicMock()
            proc.as_dict.return_value = {'pid': pid, 'name': name, 'username': 'user'}
            proc.memory_info.return_value.vms = vms_bytes
            return proc

        procs = [
            make_proc(1, 'zero_mem',   0),
            make_proc(2, 'normal_mem', 32 * 1024 * 1024),
        ]

        with patch('lash.plugins.monitor.core.ps.process_iter', return_value=procs):
            result = getListOfProcessSortedByMemory()

        assert result[0]['name'] == 'normal_mem'
        assert result[1]['name'] == 'zero_mem'
        assert result[1]['vms'] == pytest.approx(0.0)

    def test_memory_info_raises_no_such_process_is_skipped(self):
        from unittest.mock import MagicMock, patch
        import psutil as ps
        from lash.plugins.monitor.core import getListOfProcessSortedByMemory

        # process disappears between as_dict and memory_info
        bad_proc = MagicMock()
        bad_proc.as_dict.return_value = {'pid': 5, 'name': 'ghost', 'username': 'user'}
        bad_proc.memory_info.side_effect = ps.NoSuchProcess(pid=5)

        good_proc = MagicMock()
        good_proc.as_dict.return_value = {'pid': 6, 'name': 'present', 'username': 'user'}
        good_proc.memory_info.return_value.vms = 12 * 1024 * 1024

        with patch('lash.plugins.monitor.core.ps.process_iter', return_value=[bad_proc, good_proc]):
            result = getListOfProcessSortedByMemory()

        assert len(result) == 1
        assert result[0]['name'] == 'present'


class TestMonitorCommand:
    def test_monitor_is_click_command(self):
        import click
        from lash.plugins.monitor.cli import monitor

        assert isinstance(monitor, click.BaseCommand)

    def test_monitor_command_name(self):
        from lash.plugins.monitor.cli import monitor

        assert monitor.name == 'monitor'

    def test_monitor_has_help_text(self):
        from lash.plugins.monitor.cli import monitor

        assert monitor.help is not None
        assert len(monitor.help) > 0
