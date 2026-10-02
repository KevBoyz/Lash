# pytest lash/plugins/file/tests/test_cli.py
import os
from click.testing import CliRunner
from lash.plugins.file.cli import organize, crypt


class TestOrganizeCmd:
    def test_organize_by_type_moves_files(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            open("doc1.pdf", "w").close()
            open("doc2.pdf", "w").close()
            result = runner.invoke(organize, [".", "-t", "pdf"])
            assert result.exit_code == 0
            assert os.path.isdir("(.pdf) Files")
            assert "doc1.pdf" in os.listdir("(.pdf) Files")
            assert "doc2.pdf" in os.listdir("(.pdf) Files")

    def test_organize_no_args_creates_folders(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(organize, ["."])
            assert result.exit_code == 0
            assert os.path.isdir("Docs")
            assert os.path.isdir("Others")

    def test_organize_does_not_touch_subfolders(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            os.makedirs("sub")
            with open(os.path.join("sub", "nested.pdf"), "w"):
                pass
            open("top.pdf", "w").close()
            result = runner.invoke(organize, [".", "-t", "pdf"])
            assert result.exit_code == 0
            assert os.path.isfile(os.path.join("sub", "nested.pdf"))
            assert "top.pdf" in os.listdir("(.pdf) Files")


class TestCryptCommand:
    def test_encrypt_file_changes_content(self):
        runner = CliRunner()
        original_content = b"hello world"
        key = "kvzis1@7y602qsxA"
        with runner.isolated_filesystem():
            with open("secret.txt", "wb") as f:
                f.write(original_content)
            result = runner.invoke(crypt, ["secret.txt", key])
            assert result.exit_code == 0
            with open("secret.txt", "rb") as f:
                encrypted = f.read()
            assert encrypted != original_content

    def test_decrypt_roundtrip(self):
        runner = CliRunner()
        original_content = b"roundtrip test data"
        key = "kvzis1@7y602qsxA"
        with runner.isolated_filesystem():
            with open("data.txt", "wb") as f:
                f.write(original_content)
            result = runner.invoke(crypt, ["data.txt", key])
            assert result.exit_code == 0
            result = runner.invoke(crypt, ["data.txt", key, "-dc"])
            assert result.exit_code == 0
            with open("data.txt", "rb") as f:
                restored = f.read()
            assert restored == original_content

    def test_encrypt_verbose_prints_message(self):
        runner = CliRunner()
        key = "kvzis1@7y602qsxA"
        with runner.isolated_filesystem():
            with open("note.txt", "wb") as f:
                f.write(b"some text")
            result = runner.invoke(crypt, ["note.txt", key, "-v"])
            assert result.exit_code == 0
            assert "encrypted" in result.output.lower()

    def test_decrypt_verbose_prints_message(self):
        runner = CliRunner()
        key = "kvzis1@7y602qsxA"
        with runner.isolated_filesystem():
            with open("note.txt", "wb") as f:
                f.write(b"some text")
            runner.invoke(crypt, ["note.txt", key])
            result = runner.invoke(crypt, ["note.txt", key, "-dc", "-v"])
            assert result.exit_code == 0
            assert "decrypted" in result.output.lower()

    def test_encrypt_folder_with_ca_flag(self):
        runner = CliRunner()
        key = "kvzis1@7y602qsxA"
        original_a = b"file alpha content"
        original_b = b"file beta content"
        with runner.isolated_filesystem():
            os.makedirs("mydir")
            with open(os.path.join("mydir", "a.txt"), "wb") as f:
                f.write(original_a)
            with open(os.path.join("mydir", "b.txt"), "wb") as f:
                f.write(original_b)
            result = runner.invoke(crypt, ["mydir", key, "-ca"])
            assert result.exit_code == 0
            with open(os.path.join("mydir", "a.txt"), "rb") as f:
                assert f.read() != original_a
            with open(os.path.join("mydir", "b.txt"), "rb") as f:
                assert f.read() != original_b

    def test_encrypt_with_ex_writes_recovery_key_next_to_file(self):
        runner = CliRunner()
        key = "kvzis1@7y602qsxA"
        with runner.isolated_filesystem():
            os.makedirs("sub")
            target = os.path.join("sub", "secret.txt")
            with open(target, "wb") as f:
                f.write(b"hello world")
            result = runner.invoke(crypt, [target, key, "-ex"])
            assert result.exit_code == 0
            assert os.path.isfile(os.path.join("sub", "recovery-key.txt"))

    def test_auto_generated_key_is_printed(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("secret.txt", "wb") as f:
                f.write(b"plaintext")
            result = runner.invoke(crypt, ["secret.txt"])
            assert result.exit_code == 0
            assert "Generated key" in result.output

    def test_auto_generated_key_roundtrips(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            original = b"roundtrip plaintext"
            with open("secret.txt", "wb") as f:
                f.write(original)
            result = runner.invoke(crypt, ["secret.txt"])
            assert result.exit_code == 0
            lines = [ln for ln in result.output.splitlines() if "Generated key:" in ln]
            assert lines
            key = lines[0].split("Generated key:")[1].strip()
            # strip rich markup residue if any
            key = key.replace("[cyan]", "").replace("[/cyan]", "").strip()
            result = runner.invoke(crypt, ["secret.txt", key, "-dc"])
            assert result.exit_code == 0
            with open("secret.txt", "rb") as f:
                assert f.read() == original

    def test_decrypt_requires_key(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("secret.txt", "wb") as f:
                f.write(b"x")
            result = runner.invoke(crypt, ["secret.txt", "-dc"])
            assert result.exit_code != 0
            assert "key is required" in result.output.lower()

    def test_invalid_key_length_rejected(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("secret.txt", "wb") as f:
                f.write(b"x")
            result = runner.invoke(crypt, ["secret.txt", "short"])
            assert result.exit_code != 0
            assert "16 characters" in result.output
