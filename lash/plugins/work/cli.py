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


@work_group.command("ls")
@click.option("--done", is_flag=True, help="Show completed tasks")
def ls(done):
    """List tasks."""
    d = data_dir()
    tasks_path = d / "tasks.json"
    state = load_state(tasks_path)
    if done:
        tasks = [t for t in state["tasks"] if t["done"]]
        if not tasks:
            click.echo("No completed tasks.")
            return
        for t in tasks:
            click.echo(f"  [done] {t['name']} ({t['done_at'][:10]})")
    else:
        tasks = [t for t in state["tasks"] if not t["done"]]
        if not tasks:
            click.echo("No pending tasks.")
            return
        for i, t in enumerate(tasks, 1):
            active = state["active"]
            marker = " *" if active and active["task_id"] == t["id"] else ""
            click.echo(f"  {i}. {t['name']}{marker}")


@work_group.command()
@click.argument("task", required=False)
@click.option("--pomo", is_flag=True, help="Enable Pomodoro mode")
@click.option("--work", "work_mins", default=25, show_default=True, type=int,
              help="Work interval (minutes)")
@click.option("--break", "break_mins", default=5, show_default=True, type=int,
              help="Break interval (minutes)")
def start(task, pomo, work_mins, break_mins):
    """Start a task. Prompts for selection if no task given."""
    d = data_dir()
    tasks_path = d / "tasks.json"
    state = load_state(tasks_path)
    if state["active"]:
        raise click.ClickException("Task already active. Stop it first.")
    pending = [t for t in state["tasks"] if not t["done"]]
    if task is None:
        if not pending:
            raise click.ClickException("No pending tasks. Use 'work add' first.")
        for i, t in enumerate(pending, 1):
            click.echo(f"  {i}. {t['name']}")
        query = click.prompt("Enter number or new task name")
    else:
        query = task
    found = find_task(pending, query)
    if found:
        task_obj = found
    else:
        try:
            task_obj = add_task(state, query)
        except ValueError as e:
            raise click.ClickException(str(e))
    start_task(state, task_obj["id"], pomo=pomo, pomo_work_mins=work_mins,
               pomo_break_mins=break_mins)
    save_state(tasks_path, state)
    if pomo:
        click.echo(f"Started: {task_obj['name']} [Pomodoro {work_mins}/{break_mins}]")
        _run_pomodoro(tasks_path, task_obj["name"], work_mins, break_mins)
    else:
        click.echo(f"Started: {task_obj['name']}")


def _run_pomodoro(tasks_path, task_name, work_mins, break_mins):
    pass  # implemented in Task 11
