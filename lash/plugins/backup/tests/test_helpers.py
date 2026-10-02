# pytest lash/plugins/backup/tests/test_helpers.py
from datetime import datetime


class TestIsValidName:
    def test_aceita_nomes_simples(self):
        from lash.plugins.backup.helpers import is_valid_name
        for name in ("mydata", "My-Data_2", "v1.0"):
            assert is_valid_name(name)

    def test_rejeita_nomes_invalidos(self):
        from lash.plugins.backup.helpers import is_valid_name
        for name in ("", "my data", "a/b", "..", ".hidden", "name.", "NUL", "com1.txt", "x" * 65):
            assert not is_valid_name(name)


class TestArchiveName:
    def test_formato_datetime_e_nome(self):
        from lash.plugins.backup.helpers import archive_name
        moment = datetime(2026, 10, 2, 14, 30, 5)
        assert archive_name("mydata", moment) == "2026-10-02_14-30-05 mydata.zip"

    def test_parse_timestamp_inverte_archive_name(self):
        from lash.plugins.backup.helpers import archive_name, parse_timestamp
        moment = datetime(2026, 10, 2, 14, 30, 5)
        assert parse_timestamp(archive_name("mydata", moment)) == moment

    def test_parse_timestamp_retorna_none_para_nome_desconhecido(self):
        from lash.plugins.backup.helpers import parse_timestamp
        assert parse_timestamp("random.zip") is None


class TestCleanPath:
    def test_retorna_none_para_texto_vazio(self):
        from lash.plugins.backup.helpers import clean_path
        assert clean_path("  ") is None
        assert clean_path('""') is None

    def test_remove_aspas_e_resolve(self, tmp_path):
        from lash.plugins.backup.helpers import clean_path
        assert clean_path(f'"{tmp_path}"') == tmp_path.resolve()


class TestFormatSize:
    def test_formata_unidades(self):
        from lash.plugins.backup.helpers import format_size
        assert format_size(512) == "512 B"
        assert format_size(1536) == "1.5 KB"
        assert format_size(5 * 1024 ** 3) == "5.0 GB"
