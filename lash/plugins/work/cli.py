import signal
import click
from lash.plugins.work.helpers import data_dir, format_duration, find_task
from lash.plugins.work.core import (
    load_state, save_state, load_sessions, append_session,
    add_task, remove_task, start_task, pause_task, stop_task,
    calc_elapsed, format_log,
)


@click.group("work", short_help="Task and time tracker")
def work_group():
    """Manage tasks and track work time."""


@work_group.command()
@click.argument("name")
def add(name):
    """Add a task to the list."""
    d = data_dir()
    tasks_path = d / "tasks.json"
    state = load_state(tasks_path)
    try:
        task = add_task(state, name)
    except ValueError as e:
        raise click.ClickException(str(e))
    save_state(tasks_path, state)
    click.echo(f"Added: {task['name']}")


@work_group.command()
@click.argument("task")
def rm(task):
    """Remove a task by name or number."""
    d = data_dir()
    tasks_path = d / "tasks.json"
    state = load_state(tasks_path)
    try:
        removed = remove_task(state, task)
    except ValueError as e:
        raise click.ClickException(str(e))
    save_state(tasks_path, state)
    click.echo(f"Removed: {removed['name']}")


def _run_pomodoro(tasks_path, task_name, work_mins, break_mins):
    pass  # implemented in Task 11
