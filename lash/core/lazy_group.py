import importlib
import click


class LazyGroup(click.Group):
    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._lazy = lazy_subcommands or {}

    def list_commands(self, ctx):
        eager = set(super().list_commands(ctx))
        return sorted(eager | set(self._lazy.keys()))

    def get_command(self, ctx, cmd_name):
        if cmd_name in self._lazy:
            module_path, attr = self._lazy[cmd_name].rsplit(':', 1)
            module = importlib.import_module(module_path)
            return getattr(module, attr)
        return super().get_command(ctx, cmd_name)
