import json
from click.testing import CliRunner


def _setup(tmp_path):
    for name, core, category, commands in [
        (
            "random",
            True,
            "Random Generators",
            {
                "random": {
                    "module": "x:y",
                    "description": "Generate randoms",
                    "requires": [],
                }
            },
        ),
        (
            "crack",
            True,
            "Crack Tools",
            {"crack": {"module": "x:y", "description": "Crack zips", "requires": []}},
        ),
        (
            "file",
            False,
            "File Tools",
            {
                "organize": {
                    "module": "x:y",
                    "description": "Organize files",
                    "requires": ["rich>=12.6.0"],
                },
                "zip": {
                    "module": "x:y",
                    "description": "ZIP tools",
                    "requires": ["pyminizip>=0.2.6"],
                },
            },
        ),
        (
            "video",
            False,
            "Video Tools",
            {
                "video": {
                    "module": "x:y",
                    "description": "Video tools",
                    "requires": ["cv2"],
                }
            },
        ),
    ]:
        d = tmp_path / name
        d.mkdir()
        manifest = {
            "name": name,
            "category": category,
            "description": f"{name} desc",
            "commands": commands,
        }
        if core:
            manifest["core"] = True
        (d / "manifest.json").write_text(json.dumps(manifest))
    return tmp_path


def _invoke(args, plugins_dir, state_file):
    from lash.core.plugin_manager import make_plugin_list_command

    cmd = make_plugin_list_command(plugins_dir=plugins_dir, state_file=state_file)
    runner = CliRunner()
    return runner.invoke(cmd, args)


class TestPluginList:
    def test_default_shows_all_categories(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / "installed.json"
        result = _invoke([], plugins_dir, state_file)
        assert result.exit_code == 0
        assert "Random Generators" in result.output
        assert "File Tools" in result.output
        assert "Video Tools" in result.output

    def test_default_shows_installed_and_not_installed_commands(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "organize": {"plugin": "file", "requires": ["rich>=12.6.0"]},
                    }
                }
            )
        )
        result = _invoke([], plugins_dir, state_file)
        assert result.exit_code == 0
        assert "+ organize" in result.output
        assert "- zip" in result.output

    def test_core_plugins_shown_as_installed(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / "installed.json"
        result = _invoke([], plugins_dir, state_file)
        assert result.exit_code == 0
        assert "+ random" in result.output
        assert "+ crack" in result.output

    def test_installed_flag_hides_not_installed(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / "installed.json"
        result = _invoke(["-i"], plugins_dir, state_file)
        assert result.exit_code == 0
        assert "Video Tools" not in result.output
        assert "Random Generators" in result.output

    def test_not_installed_flag_hides_installed(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / "installed.json"
        result = _invoke(["-ni"], plugins_dir, state_file)
        assert result.exit_code == 0
        assert "Video Tools" in result.output
        assert "Random Generators" not in result.output

    def test_not_installed_flag_shows_message_when_all_installed(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "organize": {"plugin": "file", "requires": []},
                        "zip": {"plugin": "file", "requires": []},
                        "video": {"plugin": "video", "requires": []},
                    }
                }
            )
        )
        result = _invoke(["-ni"], plugins_dir, state_file)
        assert result.exit_code == 0
        assert "All available" in result.output

    def test_installed_flag_shows_message_when_nothing_installed(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {},
                    "removed_commands": ["random", "crack"],
                }
            )
        )
        result = _invoke(["-i"], plugins_dir, state_file)
        assert result.exit_code == 0
        assert "No plugins installed" in result.output

    def test_partially_installed_plugin_shows_mixed_markers(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "organize": {"plugin": "file", "requires": []},
                    }
                }
            )
        )
        result = _invoke([], plugins_dir, state_file)
        assert "+ organize" in result.output
        assert "- zip" in result.output


class TestPanelContador:
    def test_titulo_mostra_contador_completo_para_core(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / "installed.json"
        result = _invoke([], plugins_dir, state_file)
        assert "Random Generators" in result.output
        assert "Crack Tools" in result.output

    def test_titulo_sem_contador(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / "installed.json"
        result = _invoke([], plugins_dir, state_file)
        assert "(" not in result.output


class TestTituloCapitalizado:
    def test_categoria_lowercase_fica_capitalizada(self):
        from io import StringIO

        from lash.core.plugin_manager import _render_category_panel
        from rich.console import Console

        panel = _render_category_panel("web tools", {}, set())
        buf = StringIO()
        Console(file=buf, force_terminal=True, color_system="standard").print(panel)
        assert " Web Tools " in buf.getvalue()

    def test_categoria_media_fica_media(self):
        from io import StringIO

        from lash.core.plugin_manager import _render_category_panel
        from rich.console import Console

        panel = _render_category_panel("media", {}, set())
        buf = StringIO()
        Console(file=buf, force_terminal=True, color_system="standard").print(panel)
        assert " Media " in buf.getvalue()


class TestLayoutPares:
    def test_categorias_aparecem_lado_a_lado_na_mesma_linha(self, tmp_path):
        plugins_dir = _setup(tmp_path)
        state_file = tmp_path / "installed.json"
        result = _invoke([], plugins_dir, state_file)
        assert any(
            "Crack Tools" in line and "File Tools" in line
            for line in result.output.splitlines()
        )
        assert any(
            "Random Generators" in line and "Video Tools" in line
            for line in result.output.splitlines()
        )


class TestPanelCores:
    def _render(self, commands, active_cmds, color_system="standard"):
        from io import StringIO

        from lash.core.plugin_manager import _render_category_panel
        from rich.console import Console

        panel = _render_category_panel("Cat", commands, active_cmds)
        buf = StringIO()
        Console(file=buf, force_terminal=True, color_system=color_system).print(panel)
        return buf.getvalue()

    def test_instalado_em_verde(self):
        output = self._render(
            {"installed": {"description": "d", "requires": []}},
            {"installed"},
        )
        assert "\x1b[32m+ installed" in output

    def test_nao_instalado_em_vermelho(self):
        output = self._render(
            {"missing": {"description": "d", "requires": []}},
            set(),
        )
        assert "\x1b[31m- missing" in output

    def test_descricao_sempre_branca(self):
        output = self._render(
            {"installed": {"description": "desc", "requires": []}},
            {"installed"},
        )
        assert "\x1b[37mdesc" in output

    def test_formato_marker_plugin_dois_pontos_descricao(self):
        output = self._render(
            {"installed": {"description": "desc", "requires": []}},
            {"installed"},
        )
        assert "\x1b[32m+ installed: \x1b[0m\x1b[37mdesc" in output

    def test_borda_e_titulo_verdes_quando_tudo_instalado(self):
        output = self._render(
            {"a": {"description": "d", "requires": []}},
            {"a"},
        )
        assert "\x1b[32m┌" in output
        assert "\x1b[32m Cat" in output

    def test_borda_e_titulo_vermelhos_quando_nada_instalado(self):
        output = self._render(
            {"a": {"description": "d", "requires": []}},
            set(),
        )
        assert "\x1b[31m┌" in output
        assert "\x1b[31m Cat" in output

    def test_borda_e_titulo_rosa_quando_parcial(self):
        output = self._render(
            {
                "a": {"description": "d", "requires": []},
                "b": {"description": "d", "requires": []},
            },
            {"a"},
            color_system="256",
        )
        assert "\x1b[38;5;206m┌" in output
        assert "\x1b[38;5;206m Cat" in output
