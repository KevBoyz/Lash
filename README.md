# Lash,  the py-package ![](Images/desktop.png)![](Images/lash_gif.gif)

A set of desktop tools that simplify and automate multiple processes — file handling,
image editing, scheduling, web scraping, spy tools, math, and more.

Developed as a command-line interface with Linux-style syntax: options, args, and help sections.

```bash
pip install lash          # core only
pip install lash[all]     # all optional tools
python -m lash --help
```

**[Pypi](https://pypi.org/project/lash) · [Docs](https://kevboyz.github.io/KevBoyz-Docs/sub-pages/documentations/lash/index.html) · [Docs pt-br](https://kevboyz.github.io/7562Hall/sub-pages/lash/index.html)**

![](Images/lash_print2.png)

---

## Plugin system (v1.3.0)

Lash uses an opt-in plugin architecture. The base install requires only `click` —
commands and their dependencies are installed on demand.

```bash
python -m lash plugins --available   # see what's available
python -m lash download file_tools   # install a plugin
python -m lash download device_tools --only keyhold   # install one command
python -m lash remove file_tools --cmd zip            # remove one command
```

Core commands (`random`, `crack`) are always available without any download.

---

## Docs

| File | Contents |
|---|---|
| [RUNNING.md](RUNNING.md) | Install, run, plugin usage, examples, contributing |
| [RELEASE_NOTES.md](RELEASE_NOTES.md) | Full changelog from v1.1.0 to v1.3.0 |
