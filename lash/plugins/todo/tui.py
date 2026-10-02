from __future__ import annotations

from datetime import datetime
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

from lash.plugins.todo.core import (
    accumulated_seconds,
    add_task,
    append_session,
    calc_elapsed,
    load_sessions,
    load_state,
    pause_task,
    remove_task,
    save_state,
    seven_day_totals,
    start_task,
    stop_task,
)
from lash.plugins.todo.helpers import (
    clear_records,
    data_dir,
    format_duration,
    format_minutes_short,
    resolve_data_dir,
    set_data_dir,
)


DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _fmt_created(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
    except Exception:
        return iso
    return f"{dt.day:02d} {MONTHS[dt.month - 1]} {dt.strftime('%H:%M')}"


class AddTaskModal(ModalScreen):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Container(id="modal-box"):
            yield Static("+ Add new task", id="modal-title")
            yield Input(placeholder="Task name...", id="modal-input")
            with Horizontal(id="modal-actions"):
                yield Button("Cancel", id="modal-cancel")
                yield Button("Add", id="modal-add", variant="success")

    def on_mount(self) -> None:
        self.query_one("#modal-input", Input).focus()

    @on(Button.Pressed, "#modal-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#modal-add")
    def _confirm(self) -> None:
        value = self.query_one("#modal-input", Input).value.strip()
        self.dismiss(value or None)

    @on(Input.Submitted, "#modal-input")
    def _submit(self) -> None:
        self._confirm()

    def action_cancel(self) -> None:
        self.dismiss(None)


class ConfirmModal(ModalScreen):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self._title = title
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id="modal-box"):
            yield Static(self._title, id="modal-title")
            yield Static(self._message, id="modal-message")
            with Horizontal(id="modal-actions"):
                yield Button("Cancel", id="modal-cancel")
                yield Button("Confirm", id="modal-confirm", variant="error")

    @on(Button.Pressed, "#modal-cancel")
    def _cancel(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#modal-confirm")
    def _confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class TextPromptModal(ModalScreen):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, title: str, placeholder: str, initial: str = "") -> None:
        super().__init__()
        self._title = title
        self._placeholder = placeholder
        self._initial = initial

    def compose(self) -> ComposeResult:
        with Container(id="modal-box"):
            yield Static(self._title, id="modal-title")
            yield Input(placeholder=self._placeholder, value=self._initial,
                        id="modal-input")
            with Horizontal(id="modal-actions"):
                yield Button("Cancel", id="modal-cancel")
                yield Button("Save", id="modal-add", variant="success")

    def on_mount(self) -> None:
        self.query_one("#modal-input", Input).focus()

    @on(Button.Pressed, "#modal-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#modal-add")
    def _confirm(self) -> None:
        value = self.query_one("#modal-input", Input).value.strip()
        self.dismiss(value or None)

    @on(Input.Submitted, "#modal-input")
    def _submit(self) -> None:
        self._confirm()

    def action_cancel(self) -> None:
        self.dismiss(None)


class TaskRow(Horizontal):
    can_focus = True

    BINDINGS = [
        Binding("enter", "toggle", "Start/Pause", show=False),
    ]

    def __init__(self, task: dict, active_id: str | None, elapsed_seconds: int) -> None:
        super().__init__(classes="task-row")
        self.task_data = task
        self.task_id = task["id"]
        self.active_id = active_id
        self.elapsed_seconds = elapsed_seconds
        if active_id == task["id"]:
            self.add_class("-active")

    def compose(self) -> ComposeResult:
        is_active = self.active_id == self.task_data["id"]
        has_time = self.elapsed_seconds > 0
        if is_active:
            marker, mclass = "●", "col-status -active"
        elif has_time:
            marker, mclass = "◐", "col-status -paused"
        else:
            marker, mclass = "○", "col-status"
        yield Static(self.task_data["name"], classes="col-name")
        yield Static(format_duration(self.elapsed_seconds), classes="col-time")
        yield Static(marker, classes=mclass)
        yield Static(_fmt_created(self.task_data["created_at"]), classes="col-date")

    def action_toggle(self) -> None:
        self.app.action_toggle_focused()


class CompletedRow(Horizontal):
    def __init__(self, task: dict, total_minutes: int) -> None:
        super().__init__(classes="task-row")
        self.task_data = task
        self.total_minutes = total_minutes

    def compose(self) -> ComposeResult:
        yield Static(self.task_data["name"], classes="col-name")
        time_text = format_minutes_short(self.total_minutes) if self.total_minutes else ""
        yield Static(time_text, classes="col-time")
        yield Static("✓", classes="col-status -done")
        done_at = self.task_data.get("done_at") or ""
        yield Static(_fmt_created(done_at), classes="col-date")


class BarChart(Static):
    def __init__(self, totals: list[dict]) -> None:
        super().__init__(id="chart")
        self.totals = totals

    def render(self) -> str:
        if not self.totals:
            return "[dim]No data yet.[/dim]"
        max_min = max((d["minutes"] for d in self.totals), default=0)
        if max_min <= 0:
            return "[dim]No time logged in the last 7 days.[/dim]"
        rows = 10
        bar_width = 5
        gap = 2
        matrix = []
        labels_top = []
        for d in self.totals:
            m = d["minutes"]
            filled = round((m / max_min) * rows) if max_min else 0
            matrix.append(filled)
            labels_top.append(format_minutes_short(m) if m > 0 else "")

        lines = []
        top = "".join(
            f"[yellow]{lbl.center(bar_width)}[/yellow]" + (" " * gap)
            for lbl in labels_top
        )
        lines.append(top)
        for r in range(rows, 0, -1):
            parts = []
            for filled in matrix:
                cell = "[green]█████[/green]" if filled >= r else "     "
                parts.append(cell + (" " * gap))
            lines.append("".join(parts))
        axis = "".join(("─" * bar_width) + (" " * gap) for _ in matrix)
        lines.append(axis)
        name_line = "".join(
            DAY_NAMES[d["date"].weekday()].center(bar_width) + (" " * gap)
            for d in self.totals
        )
        date_line = "".join(
            d["date"].strftime("%d %b").center(bar_width) + (" " * gap)
            for d in self.totals
        )
        lines.append(name_line)
        lines.append(date_line)
        return "\n".join(lines)


class TodoApp(App):
    CSS_PATH = "tui.tcss"
    TITLE = "lash todo"

    VIEWS = ("pending", "completed", "performance", "config")

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("1", "nav('pending')", "Pending"),
        Binding("2", "nav('completed')", "Completed"),
        Binding("3", "nav('performance')", "Performance"),
        Binding("4", "nav('config')", "Config"),
        Binding("left", "swap_pane", "Sidebar", priority=True),
        Binding("right", "swap_pane", "Main", priority=True),
        Binding("up", "pane_cycle(-1)", "Prev", priority=True, show=False),
        Binding("down", "pane_cycle(1)", "Next", priority=True, show=False),
        Binding("n", "add_task", "New"),
        Binding("f", "shortcut_finish", "Finish", show=False),
        Binding("r", "shortcut_remove", "Remove", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        d = data_dir()
        self.tasks_path = d / "tasks.json"
        self.sessions_path = d / "sessions.json"
        self.current_view = "pending"

    def compose(self) -> ComposeResult:
        with Horizontal(id="root"):
            with Vertical(id="sidebar"):
                yield Static("lash todo", id="sidebar-title")
                yield Static(
                    "manage your tasks\nand track your time",
                    id="sidebar-sub",
                )
                yield Button("⏱  Pending", id="nav-pending", classes="nav-btn -active")
                yield Button("✓  Completed", id="nav-completed", classes="nav-btn")
                yield Button("▬  Performance", id="nav-performance", classes="nav-btn")
                yield Button("⚙  Config", id="nav-config", classes="nav-btn")
                yield Static("", id="sidebar-hints")
            with Vertical(id="main"):
                yield Container(id="view-container")

    def on_mount(self) -> None:
        try:
            self.theme = "textual-dark"
        except Exception:
            pass
        self.set_interval(1.0, self._tick)
        self._update_hints()
        self._render_view()
        self.call_after_refresh(self._focus_sidebar_current)

    def _tick(self) -> None:
        if self.current_view != "pending":
            return
        state = load_state(self.tasks_path)
        active = state.get("active")
        if not active:
            return
        try:
            elapsed = calc_elapsed(active)
            tid = active["task_id"]
            for row in self.query(TaskRow):
                if row.task_data["id"] == tid:
                    time_widget = row.query(".col-time").first()
                    if time_widget:
                        time_widget.update(format_duration(elapsed))
                    break
        except Exception:
            pass

    def action_nav(self, view: str) -> None:
        self._set_view(view)

    def action_add_task(self) -> None:
        self._open_add_modal()

    def _focused_pane(self) -> str:
        node = self.focused
        while node is not None:
            nid = getattr(node, "id", None)
            if nid == "sidebar":
                return "sidebar"
            if nid == "main":
                return "main"
            node = getattr(node, "parent", None)
        return "sidebar"

    def _sidebar_buttons(self) -> list[Button]:
        buttons = []
        for bid in ("nav-pending", "nav-completed", "nav-performance", "nav-config"):
            try:
                buttons.append(self.query_one(f"#{bid}", Button))
            except Exception:
                pass
        return buttons

    def _main_focusables(self) -> list:
        widgets = []
        widgets.extend(self.query(TaskRow))
        try:
            widgets.append(self.query_one("#add-task-btn", Button))
        except Exception:
            pass
        try:
            widgets.append(self.query_one("#config-change-dir", Button))
        except Exception:
            pass
        try:
            widgets.append(self.query_one("#config-clear", Button))
        except Exception:
            pass
        return widgets

    def _focus_sidebar_current(self) -> None:
        try:
            self.query_one(f"#nav-{self.current_view}", Button).focus()
        except Exception:
            pass

    def _focus_main_first(self) -> None:
        widgets = self._main_focusables()
        if widgets:
            widgets[0].focus()

    def action_swap_pane(self) -> None:
        if self._focused_pane() == "sidebar":
            self._focus_main_first()
        else:
            self._focus_sidebar_current()

    def action_pane_cycle(self, delta: int) -> None:
        pane = self._focused_pane()
        if pane == "sidebar":
            items = self._sidebar_buttons()
        else:
            items = self._main_focusables()
        if not items:
            return
        focused = self.focused
        idx = None
        for i, w in enumerate(items):
            if w is focused:
                idx = i
                break
        if idx is None:
            items[0].focus()
            return
        new = items[(idx + delta) % len(items)]
        new.focus()
        if pane == "sidebar":
            nid = (new.id or "").removeprefix("nav-")
            if nid in self.VIEWS and nid != self.current_view:
                self._set_view(nid)

    def _focused_task_id(self) -> str | None:
        node = self.focused
        while node is not None and not isinstance(node, TaskRow):
            node = getattr(node, "parent", None)
        return node.task_id if isinstance(node, TaskRow) else None

    def action_toggle_focused(self) -> None:
        if self.current_view != "pending":
            return
        tid = self._focused_task_id()
        if not tid:
            return
        state = load_state(self.tasks_path)
        active = state.get("active")
        if active and active["task_id"] == tid:
            self._pause_or_resume(tid)
        else:
            self._start_task(tid)

    def action_shortcut_finish(self) -> None:
        if self.current_view != "pending":
            return
        state = load_state(self.tasks_path)
        active = state.get("active")
        if not active:
            self.notify("No active task.", severity="warning")
            return
        self._complete_task(active["task_id"])

    def action_shortcut_remove(self) -> None:
        if self.current_view != "pending":
            return
        tid = self._focused_task_id()
        state = load_state(self.tasks_path)
        active = state.get("active")
        if tid:
            if active and active["task_id"] == tid:
                try:
                    stop_task(state, done=False)
                    save_state(self.tasks_path, state)
                except ValueError:
                    pass
            self._delete_task(tid)
            return
        if active:
            try:
                stop_task(state, done=False)
                save_state(self.tasks_path, state)
            except ValueError:
                pass
            self._delete_task(active["task_id"])
            return
        pending = [t for t in state["tasks"] if not t["done"]]
        if not pending:
            self.notify("Nothing to remove.", severity="warning")
            return
        self._delete_task(pending[0]["id"])

    def _set_view(self, view: str) -> None:
        self.current_view = view
        for btn_id in ("nav-pending", "nav-completed", "nav-performance", "nav-config"):
            btn = self.query_one(f"#{btn_id}", Button)
            btn.remove_class("-active")
        self.query_one(f"#nav-{view}", Button).add_class("-active")
        self._update_hints()
        self._render_view()
        self.call_after_refresh(self._focus_sidebar_current)

    def _update_hints(self) -> None:
        try:
            hints = self.query_one("#sidebar-hints", Static)
        except Exception:
            return
        if self.current_view == "pending":
            hints.update(
                "n: new task\nenter: start/pause\nf: finish\nr: remove"
            )
        else:
            hints.update("")

    def _render_view(self) -> None:
        prev_task_id = self._focused_task_id()
        prev_pane = self._focused_pane() if self.focused else None
        container = self.query_one("#view-container", Container)
        container.remove_children()
        if self.current_view == "pending":
            container.mount(self._build_pending())
        elif self.current_view == "completed":
            container.mount(self._build_completed())
        elif self.current_view == "performance":
            container.mount(self._build_performance())
        else:
            container.mount(self._build_config())
        if self.current_view == "pending" and prev_pane == "main":
            self.call_after_refresh(
                lambda: self._restore_main_focus(prev_task_id)
            )

    def _restore_main_focus(self, task_id: str | None) -> None:
        rows = list(self.query(TaskRow))
        if task_id:
            for row in rows:
                if row.task_id == task_id:
                    row.focus()
                    return
        if rows:
            rows[0].focus()
            return
        try:
            self.query_one("#add-task-btn", Button).focus()
        except Exception:
            pass

    def _build_pending(self) -> Container:
        state = load_state(self.tasks_path)
        active = state.get("active")
        active_id = active["task_id"] if active else None
        pending = [t for t in state["tasks"] if not t["done"]]

        header = Horizontal(
            Static("⏰ Main — tasks", classes="panel-title"),
            Button("+ Add task", id="add-task-btn"),
            classes="panel-header",
        )
        if not pending:
            body = Static(
                "No pending tasks. Press 'n' or click '+ Add task'.",
                id="empty-pending",
            )
        else:
            rows = []
            for t in pending:
                if active and active["task_id"] == t["id"]:
                    elapsed = calc_elapsed(active)
                else:
                    elapsed = accumulated_seconds(t)
                rows.append(TaskRow(t, active_id, elapsed))
            body = VerticalScroll(*rows)
        return Container(header, body, classes="panel")

    def _build_completed(self) -> Container:
        state = load_state(self.tasks_path)
        done = [t for t in state["tasks"] if t["done"]]
        sessions = load_sessions(self.sessions_path)
        session_minutes: dict[str, int] = {}
        for s in sessions:
            session_minutes[s["task_id"]] = (
                session_minutes.get(s["task_id"], 0) + s.get("total_minutes", 0)
            )
        header = Static("✓ Completed", classes="panel-title")
        if not done:
            body = Static("No completed tasks yet.", id="empty-completed")
        else:
            rows = []
            for t in done:
                minutes = t.get("total_minutes")
                if minutes is None:
                    minutes = session_minutes.get(t["id"], 0)
                rows.append(CompletedRow(t, minutes))
            body = VerticalScroll(*rows)
        return Container(header, body, classes="panel")

    def _build_performance(self) -> Container:
        sessions = load_sessions(self.sessions_path)
        totals = seven_day_totals(sessions)
        total_min = sum(t["minutes"] for t in totals)
        header = Horizontal(
            Static("📊 Last 7 days", classes="panel-title"),
            Static(
                f"Total: [bold green]{format_minutes_short(total_min)}[/bold green]",
                id="perf-total",
            ),
            classes="panel-header",
        )
        chart = BarChart(totals)
        return Container(header, chart, classes="panel")

    def _build_config(self) -> Container:
        header = Static("⚙ Config", classes="panel-title")
        current = str(resolve_data_dir())
        body = Vertical(
            Static("Data folder", classes="config-label"),
            Static(current, id="config-data-path", classes="config-value"),
            Button("Change data folder…", id="config-change-dir",
                   classes="config-btn"),
            Static("", classes="config-sep"),
            Static("Danger zone", classes="config-label -danger"),
            Button("Clear all records", id="config-clear",
                   classes="config-btn -danger"),
            classes="config-body",
        )
        return Container(header, body, classes="panel")

    @on(Button.Pressed)
    def _on_button(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id == "nav-pending":
            self._set_view("pending")
        elif btn_id == "nav-completed":
            self._set_view("completed")
        elif btn_id == "nav-performance":
            self._set_view("performance")
        elif btn_id == "nav-config":
            self._set_view("config")
        elif btn_id == "add-task-btn":
            self._open_add_modal()
        elif btn_id == "config-change-dir":
            self._open_change_dir_modal()
        elif btn_id == "config-clear":
            self._open_clear_confirm()

    def _open_add_modal(self) -> None:
        self.push_screen(AddTaskModal(), self._handle_add_result)

    def _handle_add_result(self, name: str | None) -> None:
        if not name:
            return
        state = load_state(self.tasks_path)
        try:
            add_task(state, name)
            save_state(self.tasks_path, state)
            self._render_view()
            self.notify(f"Added: {name}")
        except ValueError as e:
            self.notify(str(e), severity="error")

    def _start_task(self, task_id: str) -> None:
        state = load_state(self.tasks_path)
        if state.get("active"):
            prev = state["active"]
            if prev["task_id"] == task_id:
                return
            try:
                entry = stop_task(state, done=False)
                if entry:
                    append_session(self.sessions_path, entry)
            except ValueError as e:
                self.notify(str(e), severity="error")
                return
        try:
            start_task(state, task_id)
            save_state(self.tasks_path, state)
            self._render_view()
        except (ValueError, StopIteration) as e:
            self.notify(str(e), severity="error")

    def _pause_or_resume(self, task_id: str) -> None:
        state = load_state(self.tasks_path)
        active = state.get("active")
        if not active or active["task_id"] != task_id:
            return
        try:
            result = pause_task(state)
            save_state(self.tasks_path, state)
            self.notify(result.capitalize())
            self._render_view()
        except ValueError as e:
            self.notify(str(e), severity="error")

    def _complete_task(self, task_id: str) -> None:
        state = load_state(self.tasks_path)
        active = state.get("active")
        if not active or active["task_id"] != task_id:
            try:
                start_task(state, task_id)
            except (ValueError, StopIteration) as e:
                self.notify(str(e), severity="error")
                return
        try:
            entry = stop_task(state, done=True)
            save_state(self.tasks_path, state)
            if entry:
                append_session(self.sessions_path, entry)
                self.notify(
                    f"Done: {entry['task_name']} "
                    f"({format_duration(entry['total_minutes'] * 60)})"
                )
            self._render_view()
        except ValueError as e:
            self.notify(str(e), severity="error")

    def _delete_task(self, task_id: str) -> None:
        state = load_state(self.tasks_path)
        try:
            task = next(t for t in state["tasks"] if t["id"] == task_id)
            remove_task(state, task["name"])
            save_state(self.tasks_path, state)
            self.notify(f"Removed: {task['name']}", severity="warning")
            self._render_view()
        except (ValueError, StopIteration) as e:
            self.notify(str(e), severity="error")

    def _open_change_dir_modal(self) -> None:
        current = str(resolve_data_dir())
        self.push_screen(
            TextPromptModal("Change data folder", "Absolute path…", current),
            self._handle_change_dir,
        )

    def _handle_change_dir(self, value: str | None) -> None:
        if not value:
            return
        try:
            new_dir = set_data_dir(Path(value))
        except OSError as e:
            self.notify(f"Failed: {e}", severity="error")
            return
        self.tasks_path = new_dir / "tasks.json"
        self.sessions_path = new_dir / "sessions.json"
        self.notify(f"Data folder: {new_dir}")
        self._render_view()

    def _open_clear_confirm(self) -> None:
        self.push_screen(
            ConfirmModal(
                "Clear all records",
                "This will erase every task and session. Cannot be undone.",
            ),
            self._handle_clear_confirm,
        )

    def _handle_clear_confirm(self, confirmed: bool) -> None:
        if not confirmed:
            return
        try:
            clear_records(resolve_data_dir())
        except OSError as e:
            self.notify(f"Failed: {e}", severity="error")
            return
        self.notify("All records cleared.", severity="warning")
        self._render_view()


def run_app() -> None:
    TodoApp().run()
