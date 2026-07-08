import importlib
import sys
import click


class LazyGroup(click.Group):
    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._lazy = lazy_subcommands or {}

    def _module_path(self, cmd_name):
        entry = self._lazy[cmd_name]
        return entry['module'] if isinstance(entry, dict) else entry

    def _cmd_help(self, cmd_name):
        entry = self._lazy[cmd_name]
        return entry.get('description', '') if isinstance(entry, dict) else ''

    def list_commands(self, ctx):
        eager = set(super().list_commands(ctx))
        return sorted(eager | set(self._lazy.keys()))

    def get_command(self, ctx, cmd_name):
        if cmd_name in self._lazy:
            module_path, attr = self._module_path(cmd_name).rsplit(':', 1)
            try:
                module = importlib.import_module(module_path)
                return getattr(module, attr)
            except ModuleNotFoundError:
                if module_path in sys.modules:
                    del sys.modules[module_path]

                def _broken_cb():
                    click.echo(
                        f"Error: Command '{cmd_name}' requires missing dependencies.\n"
                        f"Run 'lash plugin fix' to automatically install required packages.",
                        err=True
                    )
                return click.Command(cmd_name, callback=_broken_cb)
        return super().get_command(ctx, cmd_name)

    def format_commands(self, ctx, formatter):
        rows = []
        for cmd_name in self.list_commands(ctx):
            if cmd_name in self._lazy:
                rows.append((cmd_name, self._cmd_help(cmd_name)))
            else:
                cmd = super().get_command(ctx, cmd_name)
                if cmd is None or cmd.hidden:
                    continue
                rows.append((cmd_name, cmd.get_short_help_str(limit=formatter.width)))
        if rows:
            with formatter.section('Commands'):
                formatter.write_dl(rows)
