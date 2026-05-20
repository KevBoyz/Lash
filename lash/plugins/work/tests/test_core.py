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
