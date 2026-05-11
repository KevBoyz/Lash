# pytest lash/plugins/work/tests/test_cli.py
import os
import pytest
from click.testing import CliRunner
from lash.plugins.work.cli import work


class TestWorkStartFlag:
    def test_s_creates_cache_and_prints_starting_at(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(work, ['-s'])
            assert result.exit_code == 0
            assert 'Starting at' in result.output
            assert os.path.exists('cache.json')

    def test_s_creates_work_csv(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(work, ['-s'])
            assert result.exit_code == 0
            assert os.path.exists('work.csv')
            with open('work.csv') as f:
                header = f.readline()
            assert 'date' in header
            assert 'minutes' in header


class TestWorkEndFlag:
    def test_e_without_cache_raises(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(work, ['-e'])
            assert result.exit_code != 0 or result.exception is not None

    def test_e_with_sv_does_not_save(self):
        pd = pytest.importorskip('pandas')
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(work, ['-s'])
            result = runner.invoke(work, ['-e', '-sv'])
            assert result.exit_code == 0
            assert 'Time worked' in result.output
            assert os.path.exists('cache.json')
            df = pd.read_csv('work.csv')
            assert len(df) == 0

    def test_e_saves_session_by_default(self):
        pd = pytest.importorskip('pandas')
        runner = CliRunner()
        with runner.isolated_filesystem():
            runner.invoke(work, ['-s'])
            result = runner.invoke(work, ['-e'])
            assert result.exit_code == 0
            assert 'Time worked' in result.output
            df = pd.read_csv('work.csv')
            assert len(df) == 1
