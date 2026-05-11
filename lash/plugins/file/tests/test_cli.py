# pytest lash/plugins/file/tests/test_cli.py
import os
import zipfile
from pathlib import Path
from click.testing import CliRunner
from lash.plugins.file.cli import organize, zip_group


class TestOrganizeCmd:
    def test_organize_by_type_moves_files(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            open('doc1.pdf', 'w').close()
            open('doc2.pdf', 'w').close()
            result = runner.invoke(organize, ['.', '-t', 'pdf'])
            assert result.exit_code == 0
            assert os.path.isdir('(.pdf) Files')
            assert 'doc1.pdf' in os.listdir('(.pdf) Files')
            assert 'doc2.pdf' in os.listdir('(.pdf) Files')

    def test_organize_no_args_creates_folders(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(organize, ['.'])
            assert result.exit_code == 0
            assert os.path.isdir('Docs')
            assert os.path.isdir('Others')


class TestZipView:
    def test_view_lists_files_in_zip(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            zf = zipfile.ZipFile('test.zip', 'w')
            zf.writestr('hello.txt', 'hi')
            zf.close()
            result = runner.invoke(zip_group, ['view', 'test.zip'])
            assert result.exit_code == 0
            assert 'hello.txt' in result.output


class TestZipExtract:
    def test_extract_creates_file(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            zf = zipfile.ZipFile('test.zip', 'w')
            zf.writestr('hello.txt', 'hi')
            zf.close()
            result = runner.invoke(zip_group, ['extract', 'test.zip'])
            assert result.exit_code == 0
            assert 'Process completed' in result.output
