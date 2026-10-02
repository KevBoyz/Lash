# pytest lash/plugins/backup/tests/test_core.py
import json
import zipfile
from datetime import datetime


def _make_source(tmp_path):
    source = tmp_path / "origin"
    (source / "sub").mkdir(parents=True)
    (source / "empty").mkdir()
    (source / "a.txt").write_text("hello")
    (source / "sub" / "b.txt").write_text("world")
    return source


def _registry():
    return {"records": {}}


class TestLoadRegistry:
    def test_retorna_registro_vazio_quando_arquivo_nao_existe(self, tmp_path):
        from lash.plugins.backup.core import load_registry
        assert load_registry(tmp_path / "registry.json") == {"records": {}}

    def test_levanta_erro_quando_json_corrompido(self, tmp_path):
        from lash.plugins.backup.core import BackupError, load_registry
        import pytest
        path = tmp_path / "registry.json"
        path.write_text("{not json", encoding="utf-8")
        with pytest.raises(BackupError):
            load_registry(path)

    def test_levanta_erro_quando_formato_invalido(self, tmp_path):
        from lash.plugins.backup.core import BackupError, load_registry
        import pytest
        path = tmp_path / "registry.json"
        path.write_text(json.dumps({"records": []}), encoding="utf-8")
        with pytest.raises(BackupError):
            load_registry(path)

    def test_save_e_load_preservam_dados(self, tmp_path):
        from lash.plugins.backup.core import load_registry, save_registry
        path = tmp_path / "nested" / "registry.json"
        data = {"records": {"x": {"source": "a", "destination": "b"}}}
        save_registry(path, data)
        assert load_registry(path) == data


class TestRegisterEntry:
    def test_registra_com_destino_informado(self, tmp_path):
        from lash.plugins.backup.core import register_entry
        source = _make_source(tmp_path)
        dest = tmp_path / "dest"
        registry = _registry()
        entry = register_entry(registry, "mydata", str(source), str(dest))
        assert entry["source"] == str(source.resolve())
        assert entry["destination"] == str(dest.resolve())
        assert entry["last_backup"] is None
        assert registry["records"]["mydata"] is entry

    def test_destino_padrao_e_pasta_backups_ao_lado_da_origem(self, tmp_path):
        from lash.plugins.backup.core import register_entry
        source = _make_source(tmp_path)
        entry = register_entry(_registry(), "mydata", str(source))
        assert entry["destination"] == str((tmp_path / "backups").resolve())

    def test_remove_aspas_do_caminho(self, tmp_path):
        from lash.plugins.backup.core import register_entry
        source = _make_source(tmp_path)
        entry = register_entry(_registry(), "mydata", f'"{source}"')
        assert entry["source"] == str(source.resolve())

    def test_levanta_erro_quando_nome_duplicado_ignorando_caixa(self, tmp_path):
        from lash.plugins.backup.core import BackupError, register_entry
        import pytest
        source = _make_source(tmp_path)
        registry = _registry()
        register_entry(registry, "mydata", str(source))
        with pytest.raises(BackupError):
            register_entry(registry, "MyData", str(source))

    def test_levanta_erro_quando_nome_invalido(self, tmp_path):
        from lash.plugins.backup.core import BackupError, register_entry
        import pytest
        source = _make_source(tmp_path)
        for bad in ("my data", "../x", "a/b", "con", "name.", ""):
            with pytest.raises(BackupError):
                register_entry(_registry(), bad, str(source))

    def test_levanta_erro_quando_origem_nao_existe(self, tmp_path):
        from lash.plugins.backup.core import BackupError, register_entry
        import pytest
        with pytest.raises(BackupError):
            register_entry(_registry(), "mydata", str(tmp_path / "missing"))

    def test_levanta_erro_quando_origem_e_arquivo(self, tmp_path):
        from lash.plugins.backup.core import BackupError, register_entry
        import pytest
        file = tmp_path / "file.txt"
        file.write_text("x")
        with pytest.raises(BackupError):
            register_entry(_registry(), "mydata", str(file))

    def test_levanta_erro_quando_destino_dentro_da_origem(self, tmp_path):
        from lash.plugins.backup.core import BackupError, register_entry
        import pytest
        source = _make_source(tmp_path)
        with pytest.raises(BackupError):
            register_entry(_registry(), "mydata", str(source), str(source / "bk"))

    def test_levanta_erro_quando_destino_e_arquivo(self, tmp_path):
        from lash.plugins.backup.core import BackupError, register_entry
        import pytest
        source = _make_source(tmp_path)
        file = tmp_path / "file.txt"
        file.write_text("x")
        with pytest.raises(BackupError):
            register_entry(_registry(), "mydata", str(source), str(file))


class TestEditEntry:
    def test_renomeia_registro_e_arquivos_de_backup(self, tmp_path):
        from lash.plugins.backup.core import create_backup, edit_entry, register_entry
        source = _make_source(tmp_path)
        registry = _registry()
        entry = register_entry(registry, "mydata", str(source))
        create_backup(entry, "mydata", now=datetime(2026, 10, 2, 14, 30, 5))
        key, _ = edit_entry(registry, "mydata", new_name="work")
        assert key == "work"
        assert "mydata" not in registry["records"]
        folder = tmp_path / "backups" / "work"
        assert (folder / "2026-10-02_14-30-05 work.zip").is_file()
        assert not (tmp_path / "backups" / "mydata").exists()

    def test_altera_origem_e_destino(self, tmp_path):
        from lash.plugins.backup.core import edit_entry, register_entry
        source = _make_source(tmp_path)
        other = tmp_path / "other"
        other.mkdir()
        registry = _registry()
        register_entry(registry, "mydata", str(source))
        _, entry = edit_entry(registry, "mydata", source=str(other),
                              destination=str(tmp_path / "far"))
        assert entry["source"] == str(other.resolve())
        assert entry["destination"] == str((tmp_path / "far").resolve())

    def test_destino_vazio_volta_ao_padrao(self, tmp_path):
        from lash.plugins.backup.core import edit_entry, register_entry
        source = _make_source(tmp_path)
        registry = _registry()
        register_entry(registry, "mydata", str(source), str(tmp_path / "far"))
        _, entry = edit_entry(registry, "mydata", destination="")
        assert entry["destination"] == str((tmp_path / "backups").resolve())

    def test_levanta_erro_quando_novo_nome_ja_existe(self, tmp_path):
        from lash.plugins.backup.core import BackupError, edit_entry, register_entry
        import pytest
        source = _make_source(tmp_path)
        registry = _registry()
        register_entry(registry, "one", str(source))
        register_entry(registry, "two", str(source))
        with pytest.raises(BackupError):
            edit_entry(registry, "one", new_name="two")

    def test_levanta_erro_quando_registro_nao_existe(self, tmp_path):
        from lash.plugins.backup.core import BackupError, edit_entry
        import pytest
        with pytest.raises(BackupError):
            edit_entry(_registry(), "ghost", new_name="x")

    def test_nao_altera_registro_quando_validacao_falha(self, tmp_path):
        from lash.plugins.backup.core import BackupError, edit_entry, register_entry
        import pytest
        source = _make_source(tmp_path)
        registry = _registry()
        register_entry(registry, "mydata", str(source))
        before = json.dumps(registry)
        with pytest.raises(BackupError):
            edit_entry(registry, "mydata", source=str(tmp_path / "missing"))
        assert json.dumps(registry) == before


class TestUnregisterEntry:
    def test_remove_registro(self, tmp_path):
        from lash.plugins.backup.core import register_entry, unregister_entry
        source = _make_source(tmp_path)
        registry = _registry()
        register_entry(registry, "mydata", str(source))
        key, _ = unregister_entry(registry, "MYDATA")
        assert key == "mydata"
        assert registry["records"] == {}

    def test_levanta_erro_quando_registro_nao_existe(self):
        from lash.plugins.backup.core import BackupError, unregister_entry
        import pytest
        with pytest.raises(BackupError):
            unregister_entry(_registry(), "ghost")


class TestCreateBackup:
    def test_cria_zip_com_nome_datetime_e_registro(self, tmp_path):
        from lash.plugins.backup.core import create_backup, register_entry
        source = _make_source(tmp_path)
        entry = register_entry(_registry(), "mydata", str(source))
        result = create_backup(entry, "mydata", now=datetime(2026, 10, 2, 14, 30, 5))
        expected = tmp_path / "backups" / "mydata" / "2026-10-02_14-30-05 mydata.zip"
        assert result["path"] == expected
        assert expected.is_file()
        assert result["files"] == 2
        assert result["skipped"] == []
        assert entry["last_backup"] == "2026-10-02T14:30:05"

    def test_zip_contem_arquivos_e_pastas_vazias(self, tmp_path):
        from lash.plugins.backup.core import create_backup, register_entry
        source = _make_source(tmp_path)
        entry = register_entry(_registry(), "mydata", str(source))
        result = create_backup(entry, "mydata")
        with zipfile.ZipFile(result["path"]) as zf:
            names = set(zf.namelist())
            assert zf.read("origin/a.txt") == b"hello"
        assert {"origin/a.txt", "origin/sub/b.txt", "origin/empty/"} <= names

    def test_nao_deixa_arquivo_parcial(self, tmp_path):
        from lash.plugins.backup.core import create_backup, register_entry
        source = _make_source(tmp_path)
        entry = register_entry(_registry(), "mydata", str(source))
        create_backup(entry, "mydata")
        folder = tmp_path / "backups" / "mydata"
        assert not list(folder.glob("*.partial"))

    def test_remove_arquivo_parcial_quando_interrompido(self, tmp_path):
        from lash.plugins.backup.core import create_backup, register_entry
        import pytest
        source = _make_source(tmp_path)
        entry = register_entry(_registry(), "mydata", str(source))

        def on_progress(done, total):
            if done:
                raise KeyboardInterrupt

        with pytest.raises(KeyboardInterrupt):
            create_backup(entry, "mydata", on_progress=on_progress)
        folder = tmp_path / "backups" / "mydata"
        assert list(folder.iterdir()) == []
        assert entry["last_backup"] is None

    def test_reporta_progresso_ate_o_total(self, tmp_path):
        from lash.plugins.backup.core import create_backup, register_entry
        source = _make_source(tmp_path)
        entry = register_entry(_registry(), "mydata", str(source))
        calls = []
        create_backup(entry, "mydata", on_progress=lambda d, t: calls.append((d, t)))
        assert calls[0] == (0, 10)
        assert calls[-1] == (10, 10)

    def test_levanta_erro_quando_origem_sumiu(self, tmp_path):
        from lash.plugins.backup.core import BackupError, create_backup
        import pytest
        entry = {"source": str(tmp_path / "missing"),
                 "destination": str(tmp_path / "backups")}
        with pytest.raises(BackupError):
            create_backup(entry, "mydata")

    def test_levanta_erro_quando_backup_mesmo_segundo_ja_existe(self, tmp_path):
        from lash.plugins.backup.core import BackupError, create_backup, register_entry
        import pytest
        source = _make_source(tmp_path)
        entry = register_entry(_registry(), "mydata", str(source))
        moment = datetime(2026, 10, 2, 14, 30, 5)
        create_backup(entry, "mydata", now=moment)
        with pytest.raises(BackupError):
            create_backup(entry, "mydata", now=moment)


class TestListBackups:
    def test_retorna_vazio_quando_pasta_nao_existe(self, tmp_path):
        from lash.plugins.backup.core import list_backups
        entry = {"source": str(tmp_path), "destination": str(tmp_path / "none")}
        assert list_backups(entry, "mydata") == []

    def test_lista_do_mais_novo_para_o_mais_antigo(self, tmp_path):
        from lash.plugins.backup.core import create_backup, list_backups, register_entry
        source = _make_source(tmp_path)
        entry = register_entry(_registry(), "mydata", str(source))
        create_backup(entry, "mydata", now=datetime(2026, 1, 1, 10, 0, 0))
        create_backup(entry, "mydata", now=datetime(2026, 3, 1, 10, 0, 0))
        backups = list_backups(entry, "mydata")
        assert [b["created"] for b in backups] == [
            datetime(2026, 3, 1, 10, 0, 0),
            datetime(2026, 1, 1, 10, 0, 0),
        ]
        assert all(b["size"] > 0 for b in backups)


class TestPurgeBackups:
    def test_apaga_zips_e_pasta_vazia(self, tmp_path):
        from lash.plugins.backup.core import create_backup, purge_backups, register_entry
        source = _make_source(tmp_path)
        entry = register_entry(_registry(), "mydata", str(source))
        create_backup(entry, "mydata", now=datetime(2026, 1, 1, 10, 0, 0))
        create_backup(entry, "mydata", now=datetime(2026, 1, 2, 10, 0, 0))
        assert purge_backups(entry, "mydata") == 2
        assert not (tmp_path / "backups" / "mydata").exists()

    def test_mantem_pasta_com_outros_arquivos(self, tmp_path):
        from lash.plugins.backup.core import create_backup, purge_backups, register_entry
        source = _make_source(tmp_path)
        entry = register_entry(_registry(), "mydata", str(source))
        create_backup(entry, "mydata")
        folder = tmp_path / "backups" / "mydata"
        (folder / "notes.txt").write_text("keep me")
        assert purge_backups(entry, "mydata") == 1
        assert (folder / "notes.txt").is_file()
