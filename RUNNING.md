# Running & Contributing

## Requirements

- Python >= 3.11
- pip

---

## Setup

```bash
git clone https://github.com/KevBoyz/Lash
cd Lash
python -m venv .venv
```

**Windows:**
```powershell
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

Install core dependencies:
```bash
pip install -e .
```

Install all optional dependencies:
```bash
pip install -e ".[all]"
```

---

## Run locally

```bash
lash --help
# or
python -m lash --help
```

---

## Build

```bash
pip install build
python -m build
```

Output in `dist/`:
```
dist/
├── lash-1.3.0.tar.gz
└── lash-1.3.0-py3-none-any.whl
```

---

## Publish to PyPI

```bash
pip install twine
twine upload dist/*
```

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add a plugin manifest at `lash/plugins/<plugin_name>/manifest.json`
4. Implement commands in the appropriate module under `lash/`
5. Open a pull request

Plugin manifest format:

```json
{
  "name": "my_plugin",
  "description": "Short description shown in lash plugins --available",
  "commands": {
    "mycommand": {
      "module": "lash.my_module:my_function",
      "description": "What this command does",
      "requires": ["some-package>=1.0.0"]
    }
  }
}
```

Add `"core": true` to make commands always available without `lash download`.
