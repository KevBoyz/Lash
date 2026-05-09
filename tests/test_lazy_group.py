from unittest import mock
import click
from click.testing import CliRunner


class TestLazyGroupListCommands:
    def test_returns_lazy_names_without_importing(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(name='test', lazy_subcommands={'foo': 'nonexistent_xyz:attr'})
        ctx = click.Context(group)
        # nonexistent module — proves import is never triggered
        result = group.list_commands(ctx)
        assert 'foo' in result

    def test_merges_lazy_and_eager_commands(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(name='test', lazy_subcommands={'lazy_cmd': 'os:getcwd'})

        @group.command('eager_cmd')
        def eager():
            pass

        ctx = click.Context(group)
        result = group.list_commands(ctx)
        assert 'lazy_cmd' in result
        assert 'eager_cmd' in result

    def test_result_is_sorted(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(name='test', lazy_subcommands={'zzz': 'os:getcwd', 'aaa': 'os:getcwd'})
        ctx = click.Context(group)
        result = group.list_commands(ctx)
        assert result == sorted(result)

    def test_help_does_not_import_lazy_modules(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(name='root', lazy_subcommands={'video': 'nonexistent_heavy:video'})
        runner = CliRunner()
        with mock.patch('importlib.import_module') as mock_import:
            result = runner.invoke(group, ['--help'])
            mock_import.assert_not_called()
        assert 'video' in result.output


class TestLazyGroupGetCommand:
    def test_imports_module_and_returns_attr(self):
        from lash.core.lazy_group import LazyGroup

        @click.command('mycommand')
        def mycommand():
            pass

        fake_module = mock.MagicMock()
        fake_module.mycommand = mycommand

        with mock.patch('importlib.import_module', return_value=fake_module) as mock_import:
            group = LazyGroup(name='test', lazy_subcommands={'mycommand': 'fake.module:mycommand'})
            ctx = click.Context(group)
            result = group.get_command(ctx, 'mycommand')

        mock_import.assert_called_once_with('fake.module')
        assert result is mycommand

    def test_returns_none_for_unknown_command(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(name='test', lazy_subcommands={'foo': 'os:getcwd'})
        ctx = click.Context(group)
        assert group.get_command(ctx, 'does_not_exist') is None

    def test_lazy_command_invocable_end_to_end(self):
        from lash.core.lazy_group import LazyGroup

        @click.command('greet')
        def greet():
            click.echo('hello from lazy')

        fake_module = mock.MagicMock()
        fake_module.greet = greet

        with mock.patch('importlib.import_module', return_value=fake_module):
            group = LazyGroup(name='root', lazy_subcommands={'greet': 'fake.module:greet'})
            runner = CliRunner()
            result = runner.invoke(group, ['greet'])

        assert result.exit_code == 0
        assert 'hello from lazy' in result.output
