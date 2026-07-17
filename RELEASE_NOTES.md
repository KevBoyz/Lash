# Lash — Release Notes

## v1.3.1.2 — Bugfixes, refactors and plugin manager improvements

- **plugin**: new `plugin fix` command — fixes broken imports by installing missing deps
- **plugin**: `plugin add` and `plugin remove` now support `-a`/`--all` to install/remove all
- **plugin**: `plugin add` installs one by one, continuing on failure
- **plugin**: shows the missing module name in the error message
- **work**: `work rm` got `-a`/`--all` flag; commands and texts translated from PT to EN
- **file**: `organize` translated — "Midia" → "Media"
- **web**: `news` now defaults `-t` to `True`
- **spider**: reduced timeout for faster connection scanning
- **chore**: `rich` dependency resolved

---

## v1.3.1 — Tests, refactors and new plugins

- **spider**: restructured (renamed from `spy`/`server`) with seeker daemon, file transfer, remote shell and injection client/server
- **work**: restructured start/stop/pause/status, Pomodoro with OS notifications, log with rich table, task CRUD
- **device/macro**: new plugin - record and play macros with pynput, speed control, repeat, list/rename/delete
- **crack**: ETA added to azip brute force progress
- `device` and `file`: commands grouped under their own Click group
- `image`, `video`, `web`, `audio`: `helpers.py` consolidated into `core.py`
- `audio`: `cut` and `get` rewritten with direct ffmpeg (no pytube)
- `web`/CI: pytube substituído por yt-dlp em todos os plugins
- Help texts multi-linha adicionados em todos os plugins
- Fixes: image filter aliases, device path traversal, pynput leak, calc Qt5Agg backend, plugin install spinner

---

## v1.3.0 — Plugin architecture & Performace improvements

* Plugin system: command groups are now optional (instalation) and managed with `plugin` command.
* Lazy loading: startup imports only `click`; heavy dependencies load only when the command runs.
---

## v1.2.6 — General upgrades

* New command: `work` for time management
* New command `cartesian` for _math_ group
* Better clock display for _sched_ group
* Bugfix in `monitor` command
* Code review (all files)
* Some commands and functions documented
* Some commands moved to other groups

## v1.2.5 — Web scraping

* Read Wikipedia articles/summaries with `wiki`
* Read top news using `news` (Google News)
* `yt` moved to _web_ group, new feature: `-list`
* Commands `new`, `taskkiller`, and `getconfig` removed

## v1.2.4 — Media support

* Download music/videos with `yt`
* Edit audio files with `audio`: cut, get
* Edit/make videos with `video`: rec, make, resume, intro, end, cut
* Monitor system with `monitor` (TUI dashboard)
* New command for image: `make_video`
* New command for web: `mail`
* Commands styled with Rich
* `ghscrape` bug fix

## v1.2.3 — Bug fix and math

* Error handling in `spy injection`
* New command for calc: `binomial`
* New command for calc: `trinomial`
* Graph plotting for math functions

## v1.2.2 — Spy upgrades

* New command: `spy injection` — remote command injection host/client
* Confidentiality error fixed in `spy crypt`

## v1.2.1 — Image upgrades

* New command for image: `adjust`
* New options for image: `-all`, `-c`
* Load bar on image commands

## v1.2.0 — General upgrades

* Image handling: Flip, Resize
* _Sched_ group: better syntax and display
* _Zip_ group: better syntax, display, and new options
* `spy crypt`: better syntax, new options (`-cl`, `-ex`)
* `autoclick`: single and double click only
* `web new` fixed
* `random` upgraded: sequences with numbers, letters, and specials
* New `web` command: `ghscrape` — scrape a GitHub profile
* New `zip` command: `zipview` — list files inside a zip archive

## v1.1.3 — Bug fix

* Help text sections updated
* `web new` now creates template files from string in `config.py`
* New command: `getconfig`
* `beep.wav` and `web_pkg.zip` removed from package
* `.zip.zip` error fixed in zip extract
* Licence classifier added to `setup.py`
* `-o` option added to `autoclick` (single click only)

## v1.1.2 — Bug fix

* `autoclick` function fixed

## v1.1.1 — Encryption

* New feature: encrypt/decrypt files with `spy crypt`
* Licence error fix

## v1.1.0 — Bug fix and upgrades

* Bug fixes in `zip compress/extract`, `calc prob`, `organize`, `web new`
* `configs` system added
* `task-killer` command added
* Licence changed to GNU GPLv3
* `log` renamed to `spy`
* `sched` upgrades: multi-time `run`, new `exec` and `wait` subcommands
