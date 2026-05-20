import pytest
from click.testing import CliRunner


@pytest.fixture
def work_dir(tmp_path, monkeypatch):
    d = tmp_path / "work"
    d.mkdir()
    monkeypatch.setattr("lash.plugins.work.cli.data_dir", lambda: d)
    return d


class TestAddCommand:
    def test_adiciona_tarefa(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        result = runner.invoke(work_group, ["add", "minha tarefa"])
        assert result.exit_code == 0
        assert "Added: minha tarefa" in result.output

    def test_persiste_em_disco(self, work_dir):
        import json
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["add", "persistida"])
        state = json.loads((work_dir / "tasks.json").read_text())
        assert any(t["name"] == "persistida" for t in state["tasks"])

    def test_erro_nome_duplicado(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["add", "duplicada"])
        result = runner.invoke(work_group, ["add", "duplicada"])
        assert result.exit_code != 0
        assert "already exists" in result.output


class TestRmCommand:
    def test_remove_por_nome(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["add", "remover"])
        result = runner.invoke(work_group, ["rm", "remover"])
        assert result.exit_code == 0
        assert "Removed: remover" in result.output

    def test_remove_por_numero(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["add", "primeira"])
        runner.invoke(work_group, ["add", "segunda"])
        result = runner.invoke(work_group, ["rm", "1"])
        assert result.exit_code == 0
        assert "primeira" in result.output

    def test_erro_nao_encontrada(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        result = runner.invoke(work_group, ["rm", "inexistente"])
        assert result.exit_code != 0
