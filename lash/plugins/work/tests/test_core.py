class TestLoadState:
    def test_retorna_estado_vazio_se_arquivo_nao_existe(self, tmp_path):
        from lash.plugins.work.core import load_state
        state = load_state(tmp_path / "tasks.json")
        assert state == {"tasks": [], "active": None}

    def test_carrega_estado_existente(self, tmp_path):
        import json
        from lash.plugins.work.core import load_state
        path = tmp_path / "tasks.json"
        data = {"tasks": [{"id": "1", "name": "test"}], "active": None}
        path.write_text(json.dumps(data))
        assert load_state(path) == data


class TestSaveState:
    def test_salva_e_recarrega(self, tmp_path):
        import json
        from lash.plugins.work.core import save_state
        path = tmp_path / "tasks.json"
        state = {"tasks": [], "active": None}
        save_state(path, state)
        assert json.loads(path.read_text()) == state


class TestLoadSessions:
    def test_retorna_lista_vazia_se_arquivo_nao_existe(self, tmp_path):
        from lash.plugins.work.core import load_sessions
        assert load_sessions(tmp_path / "sessions.json") == []

    def test_carrega_sessoes_existentes(self, tmp_path):
        import json
        from lash.plugins.work.core import load_sessions
        path = tmp_path / "sessions.json"
        data = [{"task_name": "test", "total_minutes": 30}]
        path.write_text(json.dumps(data))
        assert load_sessions(path) == data


class TestAppendSession:
    def test_acrescenta_a_arquivo_existente(self, tmp_path):
        import json
        from lash.plugins.work.core import append_session
        path = tmp_path / "sessions.json"
        path.write_text(json.dumps([{"task_name": "first", "total_minutes": 10}]))
        append_session(path, {"task_name": "second", "total_minutes": 20})
        result = json.loads(path.read_text())
        assert len(result) == 2
        assert result[1]["task_name"] == "second"

    def test_cria_arquivo_se_nao_existe(self, tmp_path):
        import json
        from lash.plugins.work.core import append_session
        path = tmp_path / "sessions.json"
        append_session(path, {"task_name": "first", "total_minutes": 5})
        result = json.loads(path.read_text())
        assert result == [{"task_name": "first", "total_minutes": 5}]


class TestAddTask:
    def test_adiciona_tarefa_ao_estado(self):
        from lash.plugins.work.core import add_task
        state = {"tasks": [], "active": None}
        task = add_task(state, "estudar python")
        assert len(state["tasks"]) == 1
        assert task["name"] == "estudar python"
        assert task["done"] is False
        assert task["accumulated_segments"] == []
        assert "id" in task

    def test_erro_nome_duplicado(self):
        import pytest
        from lash.plugins.work.core import add_task
        state = {"tasks": [], "active": None}
        add_task(state, "alpha")
        with pytest.raises(ValueError, match="already exists"):
            add_task(state, "alpha")

    def test_duplicado_case_insensitive(self):
        import pytest
        from lash.plugins.work.core import add_task
        state = {"tasks": [], "active": None}
        add_task(state, "Alpha")
        with pytest.raises(ValueError):
            add_task(state, "alpha")


class TestRemoveTask:
    def test_remove_por_nome(self):
        from lash.plugins.work.core import add_task, remove_task
        state = {"tasks": [], "active": None}
        add_task(state, "remover esta")
        removed = remove_task(state, "remover esta")
        assert removed["name"] == "remover esta"
        assert len(state["tasks"]) == 0

    def test_remove_por_numero(self):
        from lash.plugins.work.core import add_task, remove_task
        state = {"tasks": [], "active": None}
        add_task(state, "primeira")
        add_task(state, "segunda")
        removed = remove_task(state, "1")
        assert removed["name"] == "primeira"
        assert len(state["tasks"]) == 1

    def test_erro_tarefa_nao_encontrada(self):
        import pytest
        from lash.plugins.work.core import remove_task
        state = {"tasks": [], "active": None}
        with pytest.raises(ValueError, match="not found"):
            remove_task(state, "inexistente")

    def test_erro_remover_tarefa_ativa(self):
        import pytest
        from lash.plugins.work.core import add_task, remove_task
        state = {"tasks": [], "active": None}
        task = add_task(state, "ativa")
        state["active"] = {"task_id": task["id"], "segments": [], "current_start": None,
                           "is_paused": False, "pomo": False, "pomo_work_mins": 25,
                           "pomo_break_mins": 5, "pomo_sessions": 0}
        with pytest.raises(ValueError, match="active"):
            remove_task(state, "ativa")


class TestFormatDuration:
    def test_apenas_segundos(self):
        from lash.plugins.work.helpers import format_duration
        assert format_duration(45) == "45s"

    def test_minutos_e_segundos(self):
        from lash.plugins.work.helpers import format_duration
        assert format_duration(90) == "1m 30s"

    def test_horas_minutos_segundos(self):
        from lash.plugins.work.helpers import format_duration
        assert format_duration(3661) == "1h 01m 01s"

    def test_zero(self):
        from lash.plugins.work.helpers import format_duration
        assert format_duration(0) == "0s"


class TestFindTask:
    def test_encontra_por_indice_1based(self):
        from lash.plugins.work.helpers import find_task
        tasks = [{"name": "alpha"}, {"name": "beta"}]
        assert find_task(tasks, "1") == {"name": "alpha"}
        assert find_task(tasks, "2") == {"name": "beta"}

    def test_encontra_por_nome_case_insensitive(self):
        from lash.plugins.work.helpers import find_task
        tasks = [{"name": "Alpha"}]
        assert find_task(tasks, "alpha") == {"name": "Alpha"}
        assert find_task(tasks, "ALPHA") == {"name": "Alpha"}

    def test_retorna_none_indice_invalido(self):
        from lash.plugins.work.helpers import find_task
        assert find_task([{"name": "x"}], "5") is None

    def test_retorna_none_nome_nao_encontrado(self):
        from lash.plugins.work.helpers import find_task
        assert find_task([{"name": "x"}], "y") is None

    def test_lista_vazia(self):
        from lash.plugins.work.helpers import find_task
        assert find_task([], "1") is None
