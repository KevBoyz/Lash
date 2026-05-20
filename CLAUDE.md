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

**Plugin data storage**: `~/.lash/data/<plugin>/`  
Plugins que precisam de armazenamento persistente devem usar `~/.lash/data/<plugin>/` como diretório base. Exemplo: `~/.lash/data/work/tasks.json`. Nunca salvar dados de plugin no CWD ou em `~/.lash/` diretamente.

**LazyGroup**: commands are loaded only when invoked — keeps startup fast.

## Commands

```
lash plugin list [-i | -ni]        # list plugins by category
lash plugin add <plugin>...        # install one or more plugins
lash plugin remove <plugin>...     # uninstall one or more plugins
```

## Plugin File Distribution Rules

### Hierarquia de desenvolvimento (obrigatória)

Os arquivos crescem de forma hierárquica — cada nível só existe se o anterior precisar dele:

1. **`cli.py`** — ponto de partida sempre. Só entry points Click + output (`print`/`click.echo`). Sem lógica de negócio, sem I/O de arquivo direto.
2. **`core.py`** — criado quando `cli.py` precisa extrair funções maiores. Sem `print()` — retornar valores, deixar o cli exibir. Sem imports de Display/UI (tqdm, matplotlib interativo).
3. **`helpers.py`** — criado quando `core.py` precisa extrair funções pequenas e reutilizáveis. Ex: formatação, setup de plot, parsers genéricos.

**Direção de dependência**: `cli.py → core.py → helpers.py`. Nunca inverter.

### Regras de existência dos arquivos

- `helpers.py` **só existe se `core.py` precisar dele**. Se `core.py` estiver vazio ou trivial, mover o conteúdo de `helpers.py` para `core.py` e deletar `helpers.py`.
- `core.py` **só existe se `cli.py` precisar dele**. Plugin simples pode ter só `cli.py`.
- **Antipadrão proibido**: `helpers.py` populado + `core.py` vazio. Se encontrar isso ao revisar ou criar código, corrigir: mover tudo para `core.py`, deletar `helpers.py`.

### Ao revisar ou criar plugins — checar obrigatoriamente

- `helpers.py` existe? → `core.py` tem conteúdo substancial? Se não, consolidar.
- `core.py` existe? → `cli.py` realmente delega lógica para ele? Se não, inline no cli.
- Dependência invertida? (`core.py` importando de `cli.py`, `helpers.py` importando de `core.py`) → corrigir.

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
| device  | Device Automation | autoclick, keyhold, keylogger |
| file    | File Tools        | organize, zip, crypt          |
| image   | Image Tools       | image                         |
| monitor | System Monitor    | monitor                       |
| random  | Random Generators | random (core)                 |
| sched   | Task Scheduler    | sched                         |
| spider  | Spider Tools      | web, seeker                   |
| video   | Video Tools       | video                 |
| web     | Web Tools         | web                   |
| work    | Work Tracker      | work                  |

## Executando comandos 

Nunca tente instalar coisas no meu python global quando um comando não rodar. Todos os comandos python devem ser executados no .venv do projeto.  Execute testes usando um comando que segue o padrão:
/c/dev/Personal/Lash/.venv/Scripts/python.exe -m pytest 

Tudo relacionado a testes já esta intalado nele, não tente instalar mais nada.
Trate de não esquecer da forma exigida para executar comandos durante as seções.