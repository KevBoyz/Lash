# pytest lash/plugins/backup/tests/test_cli.py
import pytest
from click.testing import CliRunner


@pytest.fixture
def env(tmp_path, monkeypatch):
    from lash.plugins.backup import cli as backup_cli
    registry = tmp_path / "data" / "registry.json"
    monkeypatch.setattr(backup_cli, "registry_file", lambda: registry)
    source = tmp_path / "origin"
    source.mkdir()
    (source / "a.txt").write_text("hello")
    return {"tmp": tmp_path, "source": source, "registry": registry}


def _run(*args):
    from lash.plugins.backup.cli import backup
    return CliRunner().invoke(backup, list(args))


class TestRegisterCmd:
    def test_registra_e_salva_no_arquivo(self, env):
        import json
        result = _run("register", "mydata", str(env["source"]))
        assert result.exit_code == 0
        assert "Registered" in result.output
        data = json.loads(env["registry"].read_text(encoding="utf-8"))
        assert "mydata" in data["records"]

    def test_retorna_erro_quando_origem_nao_existe(self, env):
        result = _run("register", "mydata", str(env["tmp"] / "missing"))
        assert result.exit_code == 1
        assert "Error" in result.output
        assert not env["registry"].exists()

    def test_retorna_erro_quando_registro_corrompido(self, env):
        env["registry"].parent.mkdir(parents=True)
        env["registry"].write_text("{broken", encoding="utf-8")
        result = _run("register", "mydata", str(env["source"]))
        assert result.exit_code == 1
        assert "corrupted" in result.output


class TestEditCmd:
    def test_retorna_erro_sem_opcoes(self, env):
        _run("register", "mydata", str(env["source"]))
        result = _run("edit", "mydata")
        assert result.exit_code == 1
        assert "Nothing to change" in result.output

    def test_renomeia_registro(self, env):
        _run("register", "mydata", str(env["source"]))
        result = _run("edit", "mydata", "-n", "work")
        assert result.exit_code == 0
        assert "Updated" in result.output
        assert "work" in _run("list").output


class TestRemoveCmd:
    def test_remove_mantendo_backups(self, env):
        _run("register", "mydata", str(env["source"]))
        _run("do", "mydata")
        result = _run("remove", "mydata")
        assert result.exit_code == 0
        assert list((env["tmp"] / "backups" / "mydata").glob("*.zip"))

    def test_purge_apaga_backups_com_confirmacao(self, env):
        from lash.plugins.backup.cli import backup
        _run("register", "mydata", str(env["source"]))
        _run("do", "mydata")
        result = CliRunner().invoke(backup, ["remove", "mydata", "--purge"], input="y\n")
        assert result.exit_code == 0
        assert not (env["tmp"] / "backups" / "mydata").exists()

    def test_purge_cancelado_mantem_registro(self, env):
        from lash.plugins.backup.cli import backup
        _run("register", "mydata", str(env["source"]))
        _run("do", "mydata")
        result = CliRunner().invoke(backup, ["remove", "mydata", "--purge"], input="n\n")
        assert result.exit_code == 1
        assert "mydata" in _run("list").output

    def test_retorna_erro_quando_registro_nao_existe(self, env):
        result = _run("remove", "ghost")
        assert result.exit_code == 1
        assert "No backup record" in result.output


class TestDoCmd:
    def test_cria_backup(self, env):
        _run("register", "mydata", str(env["source"]))
        result = _run("do", "mydata")
        assert result.exit_code == 0
        assert "Backup created" in result.output
        zips = list((env["tmp"] / "backups" / "mydata").glob("* mydata.zip"))
        assert len(zips) == 1

    def test_retorna_erro_quando_origem_removida(self, env):
        import shutil
        _run("register", "mydata", str(env["source"]))
        shutil.rmtree(env["source"])
        result = _run("do", "mydata")
        assert result.exit_code == 1
        assert "Source folder not found" in result.output


class TestCheckCmd:
    def test_informa_quando_sem_backups(self, env):
        _run("register", "mydata", str(env["source"]))
        result = _run("check", "mydata")
        assert result.exit_code == 0
        assert "No backups found" in result.output

    def test_lista_backups(self, env):
        _run("register", "mydata", str(env["source"]))
        _run("do", "mydata")
        result = _run("check", "mydata")
        assert result.exit_code == 0
        assert "1 backup(s)" in result.output


class TestListCmd:
    def test_informa_quando_vazio(self, env):
        result = _run("list")
        assert result.exit_code == 0
        assert "No records yet" in result.output
