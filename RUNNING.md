# Running & Contributing

## Install

```bash
pip install lash          # core only (click)
pip install lash[all]     # all optional dependencies
```

## Run

```bash
python -m lash --help
```

---

## Plugin system

Lash uses an opt-in plugin system. The core install is lightweight — plugins add commands and install their own dependencies on demand.

### See what's available

```
$ python -m lash plugins --available

Core (always available):
  crack_tools
    * crack            Brute-force crack password-protected zip files
  random_tools
    * random           Generate random numbers, strings, and sequences

Not installed (run 'lash download <plugin>'):
  audio_tools          Audio editing: cut, get
  calc_tools           Math and calculus tools
  device_tools         Keyboard hold and mouse auto-click automation
  file_tools           File organization and ZIP compression tools
  image_tools          Image editing: flip, resize, adjust
  monitor_tools        System resource monitor (TUI dashboard)
  sched_tools          Task scheduling: run, wait, exec
  spy_tools            Keylogger, screenshot, and injection tools
  video_tools          Video editing and recording
  web_tools            Web scraping, YouTube download, Wikipedia, news
  work_tools           Time and task management
```

### Install a plugin

```
$ python -m lash download file_tools
Installing dependencies...
  + organize
  + zip
Done. Try: lash <command> --help
```

### Install only specific commands

```
$ python -m lash download device_tools --only keyhold
Installing dependencies...
  + keyhold
Done. Try: lash <command> --help
```

### Remove a plugin

```
$ python -m lash remove file_tools
  - organize
  - zip
Uninstalling orphaned dependencies: rich, pyminizip
Done.
```

### Remove a single command

```
$ python -m lash remove file_tools --cmd zip
  - zip
Uninstalling orphaned dependencies: pyminizip
Done.
```

---

## Examples

### Organize files by type

```
$ python -m lash download file_tools
$ python -m lash organize C:\Users\User\Documents
```

### Compress a directory

```
$ python -m lash zip compress C:\Users\User\Documents
Compacting archives, please wait...

- - Process list - -
Compacting: .gitattributes
Compacting: .gitignore
Compacting: setup.py
[...]
process completed, 206 files compacted
```

### Schedule a recurring command

```
$ python -m lash download sched_tools
$ python -m lash sched run --help
Usage: lash sched run [OPTIONS] command <hours> <minutes> <seconds>

$ python -m lash sched run "python -m lash random" 0 0 2
78311
13918
64280
[...]
Aborted!
```

### Generate a random number

```
$ python -m lash random
42917
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
