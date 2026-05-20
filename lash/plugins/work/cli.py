import signal
import click
from datetime import date
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


@work_group.command()
@click.option("--done", is_flag=True, help="Mark task as completed")
def stop(done):
    """Stop the current task."""
    d = data_dir()
    tasks_path = d / "tasks.json"
    sessions_path = d / "sessions.json"
    state = load_state(tasks_path)
    try:
        session_entry = stop_task(state, done=done)
    except ValueError as e:
        raise click.ClickException(str(e))
    save_state(tasks_path, state)
    if session_entry:
        append_session(sessions_path, session_entry)
        click.echo(f"Done: {session_entry['task_name']} ({format_duration(session_entry['total_minutes'] * 60)})")
    else:
        click.echo("Stopped.")


@work_group.command()
def pause():
    """Pause or resume the current task."""
    d = data_dir()
    tasks_path = d / "tasks.json"
    state = load_state(tasks_path)
    try:
        result = pause_task(state)
    except ValueError as e:
        raise click.ClickException(str(e))
    save_state(tasks_path, state)
    click.echo(result.capitalize() + ".")


@work_group.command()
def status():
    """Show the current task and elapsed time."""
    d = data_dir()
    tasks_path = d / "tasks.json"
    state = load_state(tasks_path)
    active = state["active"]
    if not active:
        raise click.ClickException("No active task.")
    task = next(t for t in state["tasks"] if t["id"] == active["task_id"])
    elapsed = calc_elapsed(active)
    paused = " (paused)" if active["is_paused"] else ""
    click.echo(f"Task:    {task['name']}{paused}")
    click.echo(f"Elapsed: {format_duration(elapsed)}")
    if active["pomo"]:
        click.echo(f"Pomodoro sessions: {active['pomo_sessions']}")


@work_group.command("log")
@click.option("--today", is_flag=True, help="Show only today's records")
def log(today):
    """Show time records."""
    from rich.table import Table
    from rich.console import Console
    d = data_dir()
    sessions_path = d / "sessions.json"
    sessions = load_sessions(sessions_path)
    if not sessions:
        click.echo("No records yet.")
        return
    if today:
        today_str = date.today().isoformat()
        sessions = [s for s in sessions if s["date"] == today_str]
        if not sessions:
            click.echo("No records for today.")
            return
    grouped = format_log(sessions)
    console = Console()
    for day in grouped:
        table = Table(title=day["date"])
        table.add_column("Task")
        table.add_column("Time", justify="right")
        table.add_column("Pomodoros", justify="right")
        for t in day["tasks"]:
            table.add_row(t["name"], format_duration(t["minutes"] * 60), str(t["pomo_sessions"]))
        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{format_duration(day['total_minutes'] * 60)}[/bold]",
            "",
        )
        console.print(table)


def _run_pomodoro(tasks_path, task_name, work_mins, break_mins):
    pass  # implemented in Task 11
