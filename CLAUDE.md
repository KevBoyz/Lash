# Lash — Project Guide

CLI tool built with Click + Python. Entry point: `py -m lash`.

## Structure

```
lash/
├── __init__.py          # Registers Global CLI group + plugin command
├── __main__.py          # Entry point
├── core/
│   ├── lazy_group.py    # LazyGroup: defers module import until command invoked
│   └── plugin_manager.py# Plugin CLI: add, remove, list + plugin group
└── plugins/
    ├── __init__.py      # Registry: get_available_plugins, get_lazy_commands, mark/remove command
    └── <name>/          # One package per plugin (audio, calc, crack, device, file, ...)
        ├── manifest.json
        ├── cli.py       # Entry points da interface CLI (Click commands/groups, output ao usuário)
        ├── core.py      # Grandes funções chamadas pelos entry points (lógica de negócio, I/O de arquivos)
        ├── helpers.py   # Pequenas funções utilitárias usadas pelo core.py
        └── tests/

tests/
└── core/                # Tests for lash/core/ modules
```

## Plugin System

**Discovery**: `plugins/__init__.py` scans `lash/plugins/*/manifest.json` at runtime.

**manifest.json fields**:
- `name`: plugin identifier used in `plugin add/remove` (e.g. `"audio"`)
- `category`: display group in `plugin list` (e.g. `"Audio Handlers"`)
- `core: true`: always-on, no install needed (crack, random)
- `commands`: map of `cmd_name → {module, description, requires}`
- `module`: importable path to Click object (e.g. `"lash.plugins.audio.cli:audio_group"`)

**State file**: `~/.lash/installed.json`
```json
{
  "installed_commands": { "organize": { "plugin": "file", "requires": ["rich>=12.6.0"] } },
  "removed_commands": []
}
```

**LazyGroup**: commands are loaded only when invoked — keeps startup fast.

## Commands

```
lash plugin list [-i | -ni]        # list plugins by category
lash plugin add <plugin>...        # install one or more plugins
lash plugin remove <plugin>...     # uninstall one or more plugins
```

## Plugin File Distribution Rules

Respeitar a separação entre os 3 arquivos é obrigatório:

- **`cli.py`**: só entry points Click + output (`print`/`click.echo`). Sem lógica de negócio, sem I/O de arquivo direto.
- **`core.py`**: funções grandes chamadas pelo cli. Sem `print()` — retornar valores, deixar o cli exibir. Sem imports de Display/UI (tqdm, matplotlib interativo).
- **`helpers.py`**: funções pequenas e reutilizáveis usadas pelo core. Ex: formatação, setup de plot, parsers genéricos.

**Direção de dependência**: `cli.py → core.py → helpers.py`. Nunca inverter.

## manifest.json — Regras

- `name`: deve ser idêntico ao nome do diretório do plugin
- `commands` keys: devem bater com os nomes reais dos objetos Click em `cli.py`
- `module`: formato `lash.plugins.<name>.cli:<objeto>` — verificar que o objeto existe
- `requires`: listar **todos** os pacotes third-party importados pelo plugin (incluindo transitivos usados diretamente). Ex: `rich` usado em `cli.py` deve aparecer em `requires`.
- `core: true`: só para plugins sempre ativos (crack, random)

## Tests

```
pytest tests/core/              # testa o sistema de plugins (core/)
pytest lash/plugins/<name>/tests/   # testa um plugin específico
```

No test execution during development — run only when explicitly requested.

### Convenções de testes

- Framework: pytest
- Estrutura: uma classe por feature/função testada (`class TestNomeDaFuncao`)
- Nomes de método descrevem o cenário: `test_retorna_erro_quando_fc_maior_que_pc`
- Imports dentro dos métodos de teste (padrão do projeto)
- `tmp_path` fixture para qualquer operação de filesystem — nunca tocar `~/.lash/` real
- `CliRunner` do Click para testar comandos CLI
- Importar `pytest` **apenas quando usar sua API**: `pytest.raises`, `pytest.approx`, `pytest.importorskip`, `pytest.mark`
- `pytest.approx` para comparações de float — evitar `abs(x - y) < 1e-9`
- `pytest.importorskip('pandas')` para pular testes de dependências opcionais

## Current Plugins

| Name    | Category          | Commands              |
|---------|-------------------|-----------------------|
| audio   | Audio Handlers    | audio                 |
| calc    | Calculation Tools | calc                  |
| crack   | Crack Tools       | crack (core)          |
| device  | Device Automation | autoclick, keyhold    |
| file    | File Tools        | organize, zip         |
| image   | Image Tools       | image                 |
| monitor | System Monitor    | monitor               |
| random  | Random Generators | random (core)         |
| sched   | Task Scheduler    | sched                 |
| spy     | Spy Tools         | spy                   |
| video   | Video Tools       | video                 |
| web     | Web Tools         | web                   |
| work    | Work Tracker      | work                  |
