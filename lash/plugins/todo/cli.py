import click
from lash.plugins.todo.tui import run_app


@click.command("todo", short_help="Task and time tracker (TUI)")
def todo():
    """Launch the todo TUI: tasks + time tracking."""
    run_app()
