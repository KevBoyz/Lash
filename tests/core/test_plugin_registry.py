import json


def _make_manifest(tmp_path, name, commands, core=False):
    plugin_dir = tmp_path / name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": name,
        "description": f"Test plugin {name}",
        "commands": commands,
    }
    if core:
        manifest["core"] = True
    (plugin_dir / "manifest.json").write_text(json.dumps(manifest))
    return plugin_dir


def _cmd(module, requires=None):
    return {"module": module, "description": "test", "requires": requires or []}


# Pacote que nunca existe no venv; "click" sempre existe (dep base do lash).
MISSING = "lash-dep-inexistente>=1.0"
PRESENT = "click>=8.0"


class TestGetAvailablePlugins:
    def test_reads_all_manifests(self, tmp_path):
        from lash.plugins import get_available_plugins

        _make_manifest(tmp_path, "web_tools", {"web": _cmd("lash.web_scraping:web")})
        _make_manifest(
            tmp_path, "image_tools", {"image": _cmd("lash.image_handler:image")}
        )
        result = get_available_plugins(plugins_dir=tmp_path)
        assert "web_tools" in result
        assert "image_tools" in result

    def test_ignores_dirs_without_manifest(self, tmp_path):
        from lash.plugins import get_available_plugins

        (tmp_path / "orphan_dir").mkdir()
        result = get_available_plugins(plugins_dir=tmp_path)
        assert "orphan_dir" not in result

    def test_command_data_accessible(self, tmp_path):
        from lash.plugins import get_available_plugins

        _make_manifest(
            tmp_path,
            "file_tools",
            {
                "organize": _cmd("lash.file_handler:organize", ["rich>=12.6.0"]),
                "zip": _cmd(
                    "lash.file_handler:zip_group",
                    ["pyzipper>=0.2.6", "rich>=12.6.0"],
                ),
            },
        )
        result = get_available_plugins(plugins_dir=tmp_path)
        assert (
            result["file_tools"]["commands"]["organize"]["module"]
            == "lash.file_handler:organize"
        )
        assert (
            "rich>=12.6.0" in result["file_tools"]["commands"]["organize"]["requires"]
        )


class TestGetLazyCommands:
    def test_core_commands_always_included(self, tmp_path):
        from lash.plugins import get_lazy_commands

        _make_manifest(
            tmp_path,
            "random_tools",
            {"random": _cmd("lash.ExtraTools.app_random:random")},
            core=True,
        )
        state_file = tmp_path / "installed.json"
        result = get_lazy_commands(plugins_dir=tmp_path, state_file=state_file)
        assert "random" in result
        assert result["random"]["module"] == "lash.ExtraTools.app_random:random"

    def test_comando_com_deps_presentes_no_venv_incluido(self, tmp_path):
        from lash.plugins import get_lazy_commands

        _make_manifest(
            tmp_path, "web_tools", {"web": _cmd("lash.web_scraping:web", [PRESENT])}
        )
        state_file = tmp_path / "installed.json"
        result = get_lazy_commands(plugins_dir=tmp_path, state_file=state_file)
        assert "web" in result

    def test_comando_sem_deps_incluido(self, tmp_path):
        from lash.plugins import get_lazy_commands

        _make_manifest(tmp_path, "sched", {"sched": _cmd("lash.sched:sched")})
        state_file = tmp_path / "installed.json"
        result = get_lazy_commands(plugins_dir=tmp_path, state_file=state_file)
        assert "sched" in result

    def test_comando_com_deps_faltando_excluido(self, tmp_path):
        from lash.plugins import get_lazy_commands

        _make_manifest(
            tmp_path,
            "web_tools",
            {"web": _cmd("lash.web_scraping:web", [PRESENT, MISSING])},
        )
        state_file = tmp_path / "installed.json"
        result = get_lazy_commands(plugins_dir=tmp_path, state_file=state_file)
        assert "web" not in result

    def test_instalado_no_state_mas_sem_deps_no_venv_excluido(self, tmp_path):
        from lash.plugins import get_lazy_commands

        _make_manifest(
            tmp_path, "web_tools", {"web": _cmd("lash.web_scraping:web", [MISSING])}
        )
        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "web": {"plugin": "web_tools", "requires": [MISSING]}
                    }
                }
            )
        )
        result = get_lazy_commands(plugins_dir=tmp_path, state_file=state_file)
        assert "web" not in result

    def test_comando_removido_excluido_mesmo_com_deps_presentes(self, tmp_path):
        from lash.plugins import get_lazy_commands

        _make_manifest(
            tmp_path, "web_tools", {"web": _cmd("lash.web_scraping:web", [PRESENT])}
        )
        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps({"installed_commands": {}, "removed_commands": ["web"]})
        )
        result = get_lazy_commands(plugins_dir=tmp_path, state_file=state_file)
        assert "web" not in result


class TestRequirementName:
    def test_remove_especificador_de_versao(self):
        from lash.plugins import requirement_name

        assert requirement_name("Pillow>=9.3.0") == "pillow"

    def test_formato_de_metadata_com_parenteses(self):
        from lash.plugins import requirement_name

        assert requirement_name("markdown-it-py (>=2.2.0)") == "markdown-it-py"

    def test_normaliza_underscore_e_ponto(self):
        from lash.plugins import requirement_name

        assert requirement_name("imageio_ffmpeg>=0.6.0") == "imageio-ffmpeg"
        assert requirement_name("zope.interface") == "zope-interface"

    def test_ignora_marker(self):
        from lash.plugins import requirement_name

        assert requirement_name('colorama; platform_system == "Windows"') == "colorama"


class TestProtectedPackages:
    def test_inclui_dependencias_base_do_lash(self):
        from lash.plugins import protected_packages

        protected = protected_packages()
        assert "click" in protected
        assert "rich" in protected

    def test_inclui_dependencias_transitivas_das_base(self):
        from lash.plugins import protected_packages

        assert "markdown-it-py" in protected_packages()

    def test_nao_inclui_extras(self):
        from lash.plugins import protected_packages

        assert "yt-dlp" not in protected_packages()


class TestMarkCommandInstalled:
    def test_creates_state_file_if_missing(self, tmp_path):
        from lash.plugins import mark_command_installed

        state_file = tmp_path / "installed.json"
        mark_command_installed(
            "web", "web_tools", ["bs4>=0.0.1"], state_file=state_file
        )
        assert state_file.exists()
        state = json.loads(state_file.read_text())
        assert "web" in state["installed_commands"]

    def test_preserves_existing_commands(self, tmp_path):
        from lash.plugins import mark_command_installed

        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "organize": {
                            "plugin": "file_tools",
                            "requires": [],
                        }
                    }
                }
            )
        )
        mark_command_installed(
            "zip", "file_tools", ["pyzipper>=0.2.6"], state_file=state_file
        )
        state = json.loads(state_file.read_text())
        assert "organize" in state["installed_commands"]
        assert "zip" in state["installed_commands"]


class TestRemoveCommand:
    def test_returns_orphaned_deps(self, tmp_path):
        from lash.plugins import remove_command

        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "organize": {
                            "plugin": "file_tools",
                            "requires": ["rich>=12.6.0"],
                        },
                        "zip": {
                            "plugin": "file_tools",
                            "requires": [
                                "pyzipper>=0.2.6",
                                "rich>=12.6.0",
                            ],
                        },
                    }
                }
            )
        )
        orphaned = remove_command("organize", state_file=state_file)
        assert "rich>=12.6.0" not in orphaned
        state = json.loads(state_file.read_text())
        assert "organize" not in state["installed_commands"]

    def test_returns_truly_orphaned_deps(self, tmp_path):
        from lash.plugins import remove_command

        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "organize": {
                            "plugin": "file_tools",
                            "requires": [MISSING],
                        },
                    }
                }
            )
        )
        orphaned = remove_command(
            "organize", state_file=state_file, plugins_dir=tmp_path
        )
        assert MISSING in orphaned

    def test_nunca_retorna_dependencias_base_do_lash(self, tmp_path):
        from lash.plugins import remove_command

        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "spider": {
                            "plugin": "spider",
                            "requires": ["click>=8.1.3", "rich>=12.6.0", MISSING],
                        },
                    }
                }
            )
        )
        orphaned = remove_command("spider", state_file=state_file, plugins_dir=tmp_path)
        assert orphaned == [MISSING]

    def test_preserva_dep_usada_por_comando_ativo_por_deps(self, tmp_path):
        from lash.plugins import remove_command

        _make_manifest(tmp_path, "other", {"other": _cmd("x:y", ["pytest>=1.0"])})
        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "organize": {"plugin": "file", "requires": ["pytest>=1.0"]},
                    }
                }
            )
        )
        orphaned = remove_command(
            "organize", state_file=state_file, plugins_dir=tmp_path
        )
        assert orphaned == []

    def test_marca_comando_como_removido(self, tmp_path):
        from lash.plugins import remove_command

        _make_manifest(tmp_path, "web_tools", {"web": _cmd("x:y", [PRESENT])})
        state_file = tmp_path / "installed.json"
        orphaned = remove_command("web", state_file=state_file, plugins_dir=tmp_path)
        assert orphaned == []
        state = json.loads(state_file.read_text())
        assert "web" in state["removed_commands"]

    def test_returns_empty_for_unknown_command(self, tmp_path):
        from lash.plugins import remove_command

        state_file = tmp_path / "installed.json"
        state_file.write_text(json.dumps({"installed_commands": {}}))
        orphaned = remove_command(
            "nonexistent", state_file=state_file, plugins_dir=tmp_path
        )
        assert orphaned == []
        assert "removed_commands" not in json.loads(state_file.read_text())

    def test_removes_command_from_state(self, tmp_path):
        from lash.plugins import remove_command

        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "web": {"plugin": "web_tools", "requires": ["bs4>=0.0.1"]}
                    }
                }
            )
        )
        remove_command("web", state_file=state_file)
        state = json.loads(state_file.read_text())
        assert "web" not in state["installed_commands"]


class TestRemoveCommands:
    def test_dep_compartilhada_dentro_do_lote_fica_orfa(self, tmp_path):
        from lash.plugins import remove_commands

        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "a": {"plugin": "p", "requires": [MISSING]},
                        "b": {"plugin": "p", "requires": [MISSING]},
                    }
                }
            )
        )
        orphaned = remove_commands(
            ["a", "b"], state_file=state_file, plugins_dir=tmp_path
        )
        assert orphaned == [MISSING]

    def test_dep_de_comando_ativo_fora_do_lote_preservada(self, tmp_path):
        from lash.plugins import remove_commands

        _make_manifest(tmp_path, "keep", {"keep": _cmd("x:y", ["pytest>=1.0"])})
        _make_manifest(tmp_path, "gone", {"gone": _cmd("x:y", ["pytest>=1.0"])})
        state_file = tmp_path / "installed.json"
        state_file.write_text(
            json.dumps(
                {
                    "installed_commands": {
                        "gone": {"plugin": "gone", "requires": ["pytest>=1.0"]},
                    }
                }
            )
        )
        orphaned = remove_commands(
            ["gone"], state_file=state_file, plugins_dir=tmp_path
        )
        assert orphaned == []


class TestEnvStateFile:
    def test_state_padrao_e_por_ambiente(self):
        import pathlib

        from lash.plugins import _DEFAULT_STATE_FILE

        assert _DEFAULT_STATE_FILE.parent == pathlib.Path.home() / ".lash" / "envs"
        assert _DEFAULT_STATE_FILE.suffix == ".json"
