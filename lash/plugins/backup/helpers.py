import functools
import re
from datetime import datetime
from pathlib import Path
import click
from rich.markup import escape
from rich.table import Table

TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
_TIMESTAMP_LEN = len("2000-01-01_00-00-00")
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_RESERVED_NAMES = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


class BackupError(Exception):
    """Expected failure with a message safe to show to the user."""


def guard(func):
    """Turn expected failures into a clean error message and exit code 1."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (click.exceptions.Abort, click.exceptions.Exit, click.ClickException):
            raise
        except BackupError as e:
            raise click.ClickException(str(e)) from e
        except PermissionError as e:
            raise click.ClickException(f"Permission denied: {e.filename or e}") from e
        except OSError as e:
            raise click.ClickException(f"File system error: {e}") from e
        except KeyboardInterrupt:
            raise click.ClickException("Operation cancelled by user.") from None
        except Exception as e:
            raise click.ClickException(f"Unexpected error: {e}") from e
    return wrapper


def entry_grid(name: str, source: str, backups_dir: Path) -> Table:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan")
    grid.add_column(overflow="fold")
    grid.add_row("Name", escape(name))
    grid.add_row("Source", escape(source))
    grid.add_row("Backups", escape(str(backups_dir)))
    return grid


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def is_valid_name(name: str) -> bool:
    if not _NAME_PATTERN.match(name) or name.endswith("."):
        return False
    return name.split(".")[0].lower() not in _RESERVED_NAMES


def clean_path(raw: str) -> Path | None:
    """Turn user input into an absolute path. Returns None for empty input."""
    text = raw.strip().strip("\"'").strip()
    if not text:
        return None
    return Path(text).expanduser().resolve()


def is_inside(path: Path, parent: Path) -> bool:
    return path.is_relative_to(parent)


def archive_name(name: str, moment: datetime) -> str:
    return f"{moment.strftime(TIMESTAMP_FORMAT)} {name}.zip"


def parse_timestamp(filename: str) -> datetime | None:
    try:
        return datetime.strptime(filename[:_TIMESTAMP_LEN], TIMESTAMP_FORMAT)
    except ValueError:
        return None


def format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
