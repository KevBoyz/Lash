import functools
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.markup import escape
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from lash.plugins.backup.core import (
    BackupError,
    archive_dir,
    create_backup,
    edit_entry,
    get_entry,
    list_backups,
    load_registry,
    purge_backups,
    register_entry,
    registry_file,
    save_registry,
    unregister_entry,
)
from lash.plugins.backup.helpers import format_size

_console = Console()
_err_console = Console(stderr=True)

_progress_columns = [
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    DownloadColumn(),
    TimeElapsedColumn(),
]

_MAX_SKIPPED_SHOWN = 10


def _fail(message: str) -> None:
    _err_console.print(f"[red]Error:[/red] {escape(message)}")
    sys.exit(1)


def _guard(func):
    """Turn expected failures into a clean error message and exit code 1."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (click.exceptions.Abort, click.exceptions.Exit, click.ClickException):
            raise
        except BackupError as e:
            _fail(str(e))
        except PermissionError as e:
            _fail(f"Permission denied: {e.filename or e}")
        except OSError as e:
            _fail(f"File system error: {e}")
        except KeyboardInterrupt:
            _fail("Operation cancelled by user.")
        except Exception as e:
            _fail(f"Unexpected error: {e}")
    return wrapper


def _print_entry(name: str, entry: dict) -> None:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan")
    grid.add_column(overflow="fold")
    grid.add_row("Name", escape(name))
    grid.add_row("Source", escape(entry["source"]))
    grid.add_row("Backups", escape(str(archive_dir(entry, name))))
    _console.print(grid)


@click.group("backup")
def backup():
    """Register folders and keep zipped backups of them."""


@backup.command()
@click.argument("name", metavar="<name>")
@click.argument("source", metavar="<source>")
@click.argument("destination", metavar="[destination]", required=False)
@_guard
def register(name, source, destination):
    """\b
    Register a folder to back up under a nickname.

    \b
    Backups are saved in <destination>/<name>/.
    Without a destination, a 'backups' folder next to the source is used.

    \b
    Ex:
      backup register mydata C:\\origin C:\\backup_to_here
      backup register notes ~/notes          # -> ~/backups/notes/
    """
    path = registry_file()
    registry = load_registry(path)
    entry = register_entry(registry, name, source, destination)
    save_registry(path, registry)
    _console.print(f"[green]Registered[/green] [bold]{escape(name)}[/bold]")
    _print_entry(name, entry)


@backup.command()
@click.argument("name", metavar="<name>")
@click.option("-n", "--new-name", help="Rename the record (existing backups are renamed too)")
@click.option("-s", "--source", help="New source folder")
@click.option("-d", "--dest", "destination",
              help="New destination folder ('' resets to the default)")
@_guard
def edit(name, new_name, source, destination):
    """\b
    Change the name, source or destination of a record.

    \b
    Ex:
      backup edit mydata -n work
      backup edit mydata -s D:\\new_origin -d E:\\backups
    """
    if new_name is None and source is None and destination is None:
        raise BackupError("Nothing to change. Use --new-name, --source or --dest.")
    path = registry_file()
    registry = load_registry(path)
    _, old_entry = get_entry(registry, name)
    old_entry = dict(old_entry)
    key, entry = edit_entry(registry, name, new_name=new_name,
                            source=source, destination=destination)
    save_registry(path, registry)
    _console.print(f"[green]Updated[/green] [bold]{escape(key)}[/bold]")
    _print_entry(key, entry)

    if Path(old_entry["destination"]) != Path(entry["destination"]):
        leftover = list_backups(old_entry, key)
        if leftover:
            folder = escape(str(archive_dir(old_entry, key)))
            _console.print(
                f"[yellow]Note:[/yellow] {len(leftover)} existing backup(s) "
                f"were kept in {folder}")


@backup.command()
@click.argument("name", metavar="<name>")
@click.option("-p", "--purge", is_flag=True, help="Also delete all backup files of this record")
@click.option("-y", "--yes", is_flag=True, help="Do not ask for confirmation")
@_guard
def remove(name, purge, yes):
    """\b
    Remove a record. Backup files are kept unless --purge is used.

    \b
    Ex:
      backup remove mydata
      backup remove mydata --purge
    """
    path = registry_file()
    registry = load_registry(path)
    key, entry = get_entry(registry, name)

    removed = 0
    if purge:
        backups = list_backups(entry, key)
        if backups and not yes:
            folder = archive_dir(entry, key)
            click.confirm(
                f"Delete {len(backups)} backup(s) in {folder}?", abort=True)
        removed = purge_backups(entry, key)

    unregister_entry(registry, key)
    save_registry(path, registry)
    _console.print(f"[green]Removed[/green] [bold]{escape(key)}[/bold]")
    if purge:
        _console.print(f"Deleted {removed} backup file(s).")
    else:
        folder = archive_dir(entry, key)
        if folder.is_dir():
            _console.print(f"Backup files were kept in {escape(str(folder))}")


@backup.command("do")
@click.argument("name", metavar="<name>")
@_guard
def do_backup(name):
    """\b
    Create a new zip backup of a record.

    \b
    Ex:
      backup do mydata
    """
    path = registry_file()
    registry = load_registry(path)
    key, entry = get_entry(registry, name)

    with Progress(*_progress_columns, console=_console, transient=True) as progress:
        task = progress.add_task(f"Backing up {escape(key)}", total=None)

        def on_progress(done, total):
            progress.update(task, completed=done, total=total)

        result = create_backup(entry, key, on_progress=on_progress)
    save_registry(path, registry)

    _console.print(f"[green]Backup created:[/green] {escape(str(result['path']))}")
    _console.print(
        f"{result['files']} file(s), {format_size(result['source_size'])} "
        f"-> {format_size(result['size'])}")

    skipped = result["skipped"]
    if skipped:
        _console.print(
            f"[yellow]Warning:[/yellow] {len(skipped)} item(s) could not be read and were skipped:")
        for item in skipped[:_MAX_SKIPPED_SHOWN]:
            _console.print(f"  - {escape(item)}")
        if len(skipped) > _MAX_SKIPPED_SHOWN:
            _console.print(f"  ... and {len(skipped) - _MAX_SKIPPED_SHOWN} more")


@backup.command()
@click.argument("name", metavar="<name>")
@_guard
def check(name):
    """\b
    List all backups of a record.

    \b
    Ex:
      backup check mydata
    """
    registry = load_registry(registry_file())
    key, entry = get_entry(registry, name)
    folder = archive_dir(entry, key)
    backups = list_backups(entry, key)
    if not backups:
        _console.print(
            f"[yellow]No backups found for[/yellow] [bold]{escape(key)}[/bold] "
            f"in {escape(str(folder))}")
        return

    total = sum(b["size"] for b in backups)
    table = Table(title=f"Backups of {escape(key)}")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Created", style="cyan")
    table.add_column("File", overflow="fold")
    table.add_column("Size", justify="right", style="green")
    for i, b in enumerate(backups, start=1):
        table.add_row(
            str(i),
            b["created"].strftime("%Y-%m-%d %H:%M:%S"),
            escape(b["file"]),
            format_size(b["size"]),
        )
    _console.print(table)
    _console.print(f"{len(backups)} backup(s), {format_size(total)}")
    _console.print(f"Folder: {escape(str(folder))}")


@backup.command("list")
@_guard
def list_records():
    """List all registered records."""
    registry = load_registry(registry_file())
    records = registry["records"]
    if not records:
        _console.print(
            "[yellow]No records yet.[/yellow] Use 'backup register <name> <source>' to add one.")
        return

    table = Table(title="Backup records")
    table.add_column("Name", style="bold cyan")
    table.add_column("Source", overflow="fold")
    table.add_column("Backups folder", overflow="fold")
    table.add_column("Count", justify="right")
    table.add_column("Last backup", style="green")
    for key, entry in records.items():
        source = escape(entry["source"])
        if not Path(entry["source"]).is_dir():
            source += " [red](missing)[/red]"
        last = entry.get("last_backup")
        table.add_row(
            escape(key),
            source,
            escape(str(archive_dir(entry, key))),
            str(len(list_backups(entry, key))),
            last.replace("T", " ") if last else "never",
        )
    _console.print(table)
