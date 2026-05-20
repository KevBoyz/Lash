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


class TestStopCommand:
    def test_para_tarefa_ativa(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["start", "trabalho"])
        result = runner.invoke(work_group, ["stop"])
        assert result.exit_code == 0
        assert "Done" in result.output

    def test_para_e_marca_concluida(self, work_dir):
        import json
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["start", "trabalho"])
        result = runner.invoke(work_group, ["stop"])
        assert result.exit_code == 0
        assert "Done" in result.output
        sessions = json.loads((work_dir / "sessions.json").read_text())
        assert len(sessions) == 1
        assert sessions[0]["task_name"] == "trabalho"

    def test_erro_sem_tarefa_ativa(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        result = runner.invoke(work_group, ["stop"])
        assert result.exit_code != 0


class TestPauseCommand:
    def test_pausa_tarefa_ativa(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["start", "pausar"])
        result = runner.invoke(work_group, ["pause"])
        assert result.exit_code == 0
        assert "Paused" in result.output

    def test_retoma_tarefa_pausada(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["start", "retomar"])
        runner.invoke(work_group, ["pause"])
        result = runner.invoke(work_group, ["pause"])
        assert result.exit_code == 0
        assert "Resumed" in result.output

    def test_erro_sem_tarefa(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        result = runner.invoke(work_group, ["pause"])
        assert result.exit_code != 0


class TestStatusCommand:
    def test_exibe_tarefa_ativa(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["start", "status task"])
        result = runner.invoke(work_group, ["status"])
        assert result.exit_code == 0
        assert "status task" in result.output
        assert "Elapsed" in result.output

    def test_exibe_pausado(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        runner.invoke(work_group, ["start", "pausada"])
        runner.invoke(work_group, ["pause"])
        result = runner.invoke(work_group, ["status"])
        assert "paused" in result.output

    def test_erro_sem_tarefa(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        result = runner.invoke(work_group, ["status"])
        assert result.exit_code != 0


class TestLogCommand:
    def _seed_session(self, work_dir, name="tarefa", date="2026-05-20", minutes=30, pomo=0):
        import json
        path = work_dir / "sessions.json"
        sessions = json.loads(path.read_text()) if path.exists() else []
        sessions.append({
            "task_id": "x",
            "task_name": name,
            "date": date,
            "total_minutes": minutes,
            "pomo_sessions": pomo,
            "done": True,
        })
        path.write_text(json.dumps(sessions))

    def test_sem_registros(self, work_dir):
        from lash.plugins.work.cli import work_group
        runner = CliRunner()
        result = runner.invoke(work_group, ["log"])
        assert "No records" in result.output

    def test_exibe_registros(self, work_dir):
        from lash.plugins.work.cli import work_group
        self._seed_session(work_dir, "minha tarefa", minutes=60)
        runner = CliRunner()
        result = runner.invoke(work_group, ["log"])
        assert result.exit_code == 0
        assert "minha tarefa" in result.output

    def test_filtra_hoje(self, work_dir, monkeypatch):
        from lash.plugins.work.cli import work_group
        from datetime import date
        fake_date = type("D", (), {"today": staticmethod(lambda: date(2026, 5, 20))})
        monkeypatch.setattr("lash.plugins.work.cli.date", fake_date)
        self._seed_session(work_dir, "hoje", date="2026-05-20")
        self._seed_session(work_dir, "ontem", date="2026-05-19")
        runner = CliRunner()
        result = runner.invoke(work_group, ["log", "--today"])
        assert "hoje" in result.output
        assert "ontem" not in result.output


class TestPomodoro:
    def test_start_pomo_chama_run_pomodoro(self, work_dir, monkeypatch):
        from lash.plugins.work.cli import work_group
        import lash.plugins.work.cli as cli_module
        called = {}

        def mock_pomo(tasks_path, task_name, work_mins, break_mins):
            called["task_name"] = task_name
            called["work_mins"] = work_mins
            called["break_mins"] = break_mins
        monkeypatch.setattr(cli_module, "_run_pomodoro", mock_pomo)
        runner = CliRunner()
        result = runner.invoke(work_group, ["start", "pomo task", "--pomo", "--work", "15", "--break", "3"])
        assert result.exit_code == 0
        assert called["task_name"] == "pomo task"
        assert called["work_mins"] == 15
        assert called["break_mins"] == 3

    def test_start_pomo_salva_estado_antes_do_loop(self, work_dir, monkeypatch):
        import json
        from lash.plugins.work.cli import work_group
        import lash.plugins.work.cli as cli_module
        monkeypatch.setattr(cli_module, "_run_pomodoro", lambda *a, **kw: None)
        runner = CliRunner()
        runner.invoke(work_group, ["start", "salva antes", "--pomo"])
        state = json.loads((work_dir / "tasks.json").read_text())
        assert state["active"] is not None
        assert state["active"]["pomo"] is True
