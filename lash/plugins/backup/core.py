import json
import os
import zipfile
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from lash.plugins.backup.helpers import (
    archive_name,
    clean_path,
    is_inside,
    is_valid_name,
    now_iso,
    parse_timestamp,
)


class BackupError(Exception):
    """Expected failure with a message safe to show to the user."""


def registry_file() -> Path:
    return Path.home() / ".lash" / "data" / "backup" / "registry.json"


def load_registry(path: Path) -> dict:
    if not path.exists():
        return {"records": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        raise BackupError(f"Registry file is corrupted: {path}") from e
    if not isinstance(data, dict) or not isinstance(data.get("records"), dict):
        raise BackupError(f"Registry file has an invalid format: {path}")
    return data


def save_registry(path: Path, registry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _find_key(registry: dict, name: str) -> str | None:
    target = name.casefold()
    return next((k for k in registry["records"] if k.casefold() == target), None)


def get_entry(registry: dict, name: str) -> tuple[str, dict]:
    key = _find_key(registry, name)
    if key is None:
        raise BackupError(
            f"No backup record named '{name}'. Use 'backup list' to see records.")
    return key, registry["records"][key]


def _check_name(name: str) -> None:
    if not is_valid_name(name):
        raise BackupError(
            f"Invalid name '{name}'. Use up to 64 letters, digits, '.', '_' or '-', "
            "starting with a letter or digit.")


def _check_source(raw: str | None) -> Path:
    path = clean_path(raw) if raw else None
    if path is None:
        raise BackupError("Source path cannot be empty.")
    if not path.exists():
        raise BackupError(f"Source folder not found: {path}")
    if not path.is_dir():
        raise BackupError(f"Source is not a folder: {path}")
    return path


def _default_destination(source: Path) -> Path:
    return source.parent / "backups"


def _check_destination(source: Path, destination: Path, name: str) -> None:
    if destination.exists() and not destination.is_dir():
        raise BackupError(f"Destination is not a folder: {destination}")
    target = destination / name
    if is_inside(target, source):
        raise BackupError(
            f"Backup folder '{target}' cannot be inside the source folder "
            f"'{source}'. Choose a destination outside of it.")


def archive_dir(entry: dict, name: str) -> Path:
    return Path(entry["destination"]) / name


def register_entry(registry: dict, name: str, source: str,
                   destination: str | None = None) -> dict:
    _check_name(name)
    if _find_key(registry, name) is not None:
        raise BackupError(
            f"A record named '{name}' already exists. Use 'backup edit' to change it.")
    src = _check_source(source)
    dest = (clean_path(destination) if destination else None) or _default_destination(src)
    _check_destination(src, dest, name)
    entry = {
        "source": str(src),
        "destination": str(dest),
        "created_at": now_iso(),
        "last_backup": None,
    }
    registry["records"][name] = entry
    return entry


def rename_archives(destination: Path, old_name: str, new_name: str) -> Path | None:
    """Rename the archive folder and its '<datetime> <name>.zip' files."""
    old_dir = destination / old_name
    if not old_dir.is_dir():
        return None
    new_dir = destination / new_name
    if new_dir.exists() and not os.path.samefile(old_dir, new_dir):
        raise BackupError(f"Cannot rename backups: '{new_dir}' already exists.")
    old_dir.rename(new_dir)
    old_suffix = f" {old_name}.zip"
    for path in new_dir.glob("*.zip"):
        if path.name.endswith(old_suffix):
            prefix = path.name[:-len(old_suffix)]
            path.rename(path.with_name(f"{prefix} {new_name}.zip"))
    return new_dir


def edit_entry(registry: dict, name: str, *, new_name: str | None = None,
               source: str | None = None,
               destination: str | None = None) -> tuple[str, dict]:
    """Update a record. An empty destination resets it to the default."""
    key, old = get_entry(registry, name)
    target_key = key
    if new_name is not None:
        _check_name(new_name)
        other = _find_key(registry, new_name)
        if other is not None and other != key:
            raise BackupError(f"A record named '{new_name}' already exists.")
        target_key = new_name

    src = _check_source(source) if source is not None else Path(old["source"])
    if destination is None:
        dest = Path(old["destination"])
    else:
        dest = clean_path(destination) or _default_destination(src)
    _check_destination(src, dest, target_key)

    if target_key != key:
        rename_archives(Path(old["destination"]), key, target_key)

    entry = {**old, "source": str(src), "destination": str(dest)}
    del registry["records"][key]
    registry["records"][target_key] = entry
    return target_key, entry


def unregister_entry(registry: dict, name: str) -> tuple[str, dict]:
    key, _ = get_entry(registry, name)
    return key, registry["records"].pop(key)


def scan_source(source: Path) -> tuple[list[tuple[Path, int]], list[Path], list[str]]:
    """Return (files with sizes, empty folders, unreadable paths)."""
    files, empty_dirs, skipped = [], [], []

    def on_error(err: OSError) -> None:
        skipped.append(str(err.filename))

    for dirpath, dirnames, filenames in os.walk(source, onerror=on_error):
        current = Path(dirpath)
        if not dirnames and not filenames and current != source:
            empty_dirs.append(current)
        for filename in filenames:
            path = current / filename
            try:
                size = path.stat().st_size
            except OSError:
                skipped.append(str(path))
                continue
            files.append((path, size))
    return files, empty_dirs, skipped


def create_backup(entry: dict, name: str, on_progress=None,
                  now: datetime | None = None) -> dict:
    """Zip the record's source into '<destination>/<name>/<datetime> <name>.zip'.

    on_progress(done_bytes, total_bytes) is called after each file.
    """
    source = Path(entry["source"])
    if not source.is_dir():
        raise BackupError(f"Source folder not found: {source}")
    target_dir = archive_dir(entry, name)
    if is_inside(target_dir.resolve(), source.resolve()):
        raise BackupError(
            f"Backup folder '{target_dir}' is inside the source folder. "
            "Change the destination with 'backup edit'.")

    files, empty_dirs, skipped = scan_source(source)
    total = sum(size for _, size in files)

    moment = now or datetime.now()
    target_dir.mkdir(parents=True, exist_ok=True)
    archive = target_dir / archive_name(name, moment)
    if archive.exists():
        raise BackupError(f"Backup already exists: {archive}. Try again in a second.")
    partial = archive.with_name(archive.name + ".partial")
    root = Path(source.name or name)

    written = 0
    done = 0
    if on_progress:
        on_progress(done, total)
    try:
        with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED,
                             strict_timestamps=False) as zf:
            for folder in empty_dirs:
                zf.write(folder, (root / folder.relative_to(source)).as_posix())
            for path, size in files:
                try:
                    zf.write(path, (root / path.relative_to(source)).as_posix())
                    written += 1
                except OSError:
                    skipped.append(str(path))
                done += size
                if on_progress:
                    on_progress(done, total)
        os.replace(partial, archive)
    except BaseException:
        with suppress(OSError):
            partial.unlink(missing_ok=True)
        raise

    entry["last_backup"] = moment.isoformat(timespec="seconds")
    return {
        "path": archive,
        "files": written,
        "source_size": total,
        "size": archive.stat().st_size,
        "skipped": skipped,
    }


def list_backups(entry: dict, name: str) -> list[dict]:
    """Return the record's archives, newest first."""
    folder = archive_dir(entry, name)
    if not folder.is_dir():
        return []
    backups = []
    for path in folder.glob("*.zip"):
        try:
            stat = path.stat()
        except OSError:
            continue
        created = parse_timestamp(path.name) or datetime.fromtimestamp(stat.st_mtime)
        backups.append({
            "file": path.name,
            "path": path,
            "created": created,
            "size": stat.st_size,
        })
    backups.sort(key=lambda b: b["created"], reverse=True)
    return backups


def purge_backups(entry: dict, name: str) -> int:
    """Delete the record's archives and its folder if left empty."""
    removed = 0
    for backup in list_backups(entry, name):
        backup["path"].unlink()
        removed += 1
    with suppress(OSError):
        archive_dir(entry, name).rmdir()
    return removed
