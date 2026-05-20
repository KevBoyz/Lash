# pytest lash/plugins/file/tests/test_cli.py
import os
import zipfile
from click.testing import CliRunner
from lash.plugins.file.cli import organize, zip_group, crypt


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


class TestCryptCommand:
    def test_encrypt_file_changes_content(self):
        runner = CliRunner()
        original_content = b'hello world'
        key = 'kvzis1@7y602qsxA'
        with runner.isolated_filesystem():
            with open('secret.txt', 'wb') as f:
                f.write(original_content)
            result = runner.invoke(crypt, ['secret.txt', key])
            assert result.exit_code == 0
            with open('secret.txt', 'rb') as f:
                encrypted = f.read()
            assert encrypted != original_content

    def test_decrypt_roundtrip(self):
        runner = CliRunner()
        original_content = b'roundtrip test data'
        key = 'kvzis1@7y602qsxA'
        with runner.isolated_filesystem():
            with open('data.txt', 'wb') as f:
                f.write(original_content)
            result = runner.invoke(crypt, ['data.txt', key])
            assert result.exit_code == 0
            result = runner.invoke(crypt, ['data.txt', key, '-dc'])
            assert result.exit_code == 0
            with open('data.txt', 'rb') as f:
                restored = f.read()
            assert restored == original_content

    def test_encrypt_verbose_prints_message(self):
        runner = CliRunner()
        key = 'kvzis1@7y602qsxA'
        with runner.isolated_filesystem():
            with open('note.txt', 'wb') as f:
                f.write(b'some text')
            result = runner.invoke(crypt, ['note.txt', key, '-v'])
            assert result.exit_code == 0
            assert 'encrypted' in result.output.lower()

    def test_decrypt_verbose_prints_message(self):
        runner = CliRunner()
        key = 'kvzis1@7y602qsxA'
        with runner.isolated_filesystem():
            with open('note.txt', 'wb') as f:
                f.write(b'some text')
            runner.invoke(crypt, ['note.txt', key])
            result = runner.invoke(crypt, ['note.txt', key, '-dc', '-v'])
            assert result.exit_code == 0
            assert 'decrypted' in result.output.lower()

    def test_encrypt_folder_with_cl_flag(self):
        runner = CliRunner()
        key = 'kvzis1@7y602qsxA'
        original_a = b'file alpha content'
        original_b = b'file beta content'
        with runner.isolated_filesystem():
            os.makedirs('mydir')
            with open(os.path.join('mydir', 'a.txt'), 'wb') as f:
                f.write(original_a)
            with open(os.path.join('mydir', 'b.txt'), 'wb') as f:
                f.write(original_b)
            result = runner.invoke(crypt, ['mydir', key, '-cl'])
            assert result.exit_code == 0
            with open(os.path.join('mydir', 'a.txt'), 'rb') as f:
                assert f.read() != original_a
            with open(os.path.join('mydir', 'b.txt'), 'rb') as f:
                assert f.read() != original_b
