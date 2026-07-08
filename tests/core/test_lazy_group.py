from click.testing import CliRunner


class TestLazyGroupImportError:
    def test_returns_command_when_module_not_found(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(
            name='test',
            lazy_subcommands={
                'broken': {'module': 'fully.fake.module.nonexistent:cmd', 'description': 'A broken command'},
            },
        )
        cmd = group.get_command(None, 'broken')
        assert cmd is not None
        assert cmd.name == 'broken'

    def test_shows_fix_message_on_invocation(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(
            name='test',
            lazy_subcommands={
                'broken': {'module': 'completely.missing.package:cmd', 'description': 'A broken command'},
            },
        )
        cmd = group.get_command(None, 'broken')
        runner = CliRunner()
        result = runner.invoke(cmd, [])
        assert result.exit_code == 0
        assert 'missing dependency' in result.output.lower()
        assert 'completely' in result.output
        assert 'lash plugin fix' in result.output

    def test_real_command_still_works(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(
            name='test',
            lazy_subcommands={
                'crack': {'module': 'lash.plugins.crack.cli:crack', 'description': 'Crack zips'},
            },
        )
        cmd = group.get_command(None, 'crack')
        assert cmd is not None
        assert cmd.name == 'crack'
        # Invoke --help — should NOT show the fix message
        runner = CliRunner()
        result = runner.invoke(cmd, ['--help'])
        assert result.exit_code == 0
        assert 'missing dependencies' not in result.output.lower()

    def test_non_lazy_command_returns_none(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(name='test')
        result = group.get_command(None, 'nonexistent')
        assert result is None

    def test_list_commands_still_shows_broken_commands(self):
        from lash.core.lazy_group import LazyGroup
        group = LazyGroup(
            name='test',
            lazy_subcommands={
                'broken': {'module': 'does.not.exist:cmd', 'description': 'A broken command'},
            },
        )
        commands = group.list_commands(None)
        assert 'broken' in commands
