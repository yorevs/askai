import click
from askai.core.commander.commands.SettingsCmd import SettingsCmd
from hspylib.core.tools.commons import sysout


@click.group()
@click.pass_context
def askai(ctx) -> None:
    pass


@askai.command()
def help() -> None:
    """Display this help and exit."""
    sysout(askai())


@askai.command()
@click.argument('operation', default='list')
@click.argument('key', default='')
@click.argument('value', default='')
def settings(operation: str, key: str | None = None, value: str | None = None) -> None:
    """The settings operation to perform."""
    match operation:
        case 'set':
            SettingsCmd.set(key, value)
        case 'get':
            SettingsCmd.get(key)
        case 'list':
            SettingsCmd.list(key)
        case 'reset':
            SettingsCmd.reset()
        case _:
            err = str(click.BadParameter(f"Invalid operation: '{operation}'"))
            sysout(f"\n%RED%{err}%NC%\n")
