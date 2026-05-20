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


class TestLsCommand:
    def test_lista_tarefas_pendentes(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["add", "tarefa um"])
        runner.invoke(work_group, ["add", "tarefa dois"])
        result = runner.invoke(work_group, ["ls"])
        assert result.exit_code == 0
        assert "1." in result.output
        assert "tarefa um" in result.output
        assert "2." in result.output

    def test_lista_vazia(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        result = runner.invoke(work_group, ["ls"])
        assert "No pending" in result.output

    def test_lista_concluidas_com_flag(self, work_dir):
        import json as _json
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["add", "concluida"])
        state_path = work_dir / "tasks.json"
        state = _json.loads(state_path.read_text())
        state["tasks"][0]["done"] = True
        state["tasks"][0]["done_at"] = "2026-05-20T10:00:00"
        state_path.write_text(_json.dumps(state))
        result = runner.invoke(work_group, ["ls", "--done"])
        assert "concluida" in result.output


class TestStartCommand:
    def test_inicia_por_nome(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["add", "minha tarefa"])
        result = runner.invoke(work_group, ["start", "minha tarefa"])
        assert result.exit_code == 0
        assert "Started: minha tarefa" in result.output

    def test_inicia_por_numero(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["add", "numerada"])
        result = runner.invoke(work_group, ["start", "1"])
        assert result.exit_code == 0
        assert "numerada" in result.output

    def test_cria_e_inicia_tarefa_nova(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        result = runner.invoke(work_group, ["start", "nova tarefa"])
        assert result.exit_code == 0
        assert "Started: nova tarefa" in result.output

    def test_picker_por_lista(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["add", "picker tarefa"])
        result = runner.invoke(work_group, ["start"], input="1\n")
        assert result.exit_code == 0
        assert "picker tarefa" in result.output

    def test_erro_tarefa_ja_ativa(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["start", "primeira"])
        result = runner.invoke(work_group, ["start", "segunda"])
        assert result.exit_code != 0
        assert "already active" in result.output
