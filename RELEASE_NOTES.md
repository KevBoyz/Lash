# Lash — Release Notes

## v1.3.0 — Plugin architecture & lazy loading

* **Plugin system** — tools are now optional and installed on demand via `lash download <plugin>`
* **Lazy loading** — startup imports only `click`; heavy dependencies load only when the command runs
* **Granular install** — `lash download <plugin> --only <cmd>` installs a single command and its deps
* **Plugin manager** — `lash plugins [--available]` lists installed and available plugins
* **Removal with dep cleanup** — `lash remove <plugin> [--cmd <cmd>]` uninstalls commands and orphaned packages
* **Core commands always available** — `random` and `crack` require no extra packages
* `install_requires` reduced to `click` only; all optional deps grouped under `extras_require[all]`

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
