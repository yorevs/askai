import click

from askai.core.askai_configs import configs
from askai.core.commander.commands.settings_cmd import SettingsCmd
from askai.core.commander.commands.tts_stt_cmd import TtsSttCmd
from askai.core.support.text_formatter import text_formatter

HELP_MSG = """
# AskAI Commander - HELP

> Commands:

```
  `/debug`              : toggle debugging ON/OFF.
  `/devices`            : list/set the audio input device.
  `/help`               : show this help message and exit.
  `/settings`           : list/get/set/reset settings.
  `/speak`              : toggle speaking ON/OFF.
  `/tempo`              : list/set speech-to-text tempo.
  `/voices`             : list/set/play speech-to-text voice.
```

> Keybindings:

```
  `Ctrl+G`              : toggle speaking ON/OFF.
  `Ctrl+K`              : resets the chat context.
  `Ctrl+L`              : push-To-Talk.
  `Ctrl+R`              : resets input filed.
  `Ctrl+F`              : forget the input history.
```
"""


@click.group()
@click.pass_context
def askai(ctx) -> None:
    pass


@askai.command()
def help() -> None:
    """Display this help and exit."""
    text_formatter.cmd_print(HELP_MSG)


@askai.command()
@click.argument('operation', default='list')
@click.argument('name', default='')
@click.argument('value', default='')
def settings(operation: str, name: str | None = None, value: str | None = None) -> None:
    """Manage AskAI settings.
    :param operation The operation to manage settings.
    :param name The settings key to operate.
    :param value The settings value to be set.
    """
    match operation:
        case 'list':
            SettingsCmd.list(name)
        case 'get':
            SettingsCmd.get(name)
        case 'set':
            SettingsCmd.set(name, value)
        case 'reset':
            SettingsCmd.reset()
        case _:
            err = str(click.BadParameter(f"Invalid settings operation: '{operation}'"))
            text_formatter.cmd_print(f"%RED%{err}%NC%")


@askai.command()
@click.argument('operation', default='list')
@click.argument('name', default='')
def devices(operation: str, name: str | None = None) -> None:
    """Manage the Audio Input devices.
    :param operation The operation to manage devices.
    :param name The device name to set.
    """
    match operation:
        case 'list':
            TtsSttCmd.device_list()
        case 'set':
            TtsSttCmd.device_set(name)
        case _:
            err = str(click.BadParameter(f"Invalid settings operation: '{operation}'"))
            text_formatter.cmd_print(f"%RED%{err}%NC%")


@askai.command()
@click.argument('operation', default='list')
@click.argument('name', default='onyx')
def voices(operation: str, name: str | int | None = None) -> None:
    """Manage the Text-To-Speech voices.
    :param operation The operation to manage voices.
    :param name The voice name.
    """
    match operation:
        case 'list':
            TtsSttCmd.voice_list()
        case 'set':
            TtsSttCmd.voice_set(name)
        case 'play':
            TtsSttCmd.voice_play(name)
        case _:
            err = str(click.BadParameter(f"Invalid voices operation: '{operation}'"))
            text_formatter.cmd_print(f"%RED%{err}%NC%")


@askai.command()
@click.argument('speed', type=click.INT, default=1)
def tempo(speed: int | None = None) -> None:
    """Adjust the Text-To-Speech tempo.
    :param speed The tempo to set.
    """
    TtsSttCmd.tempo(speed)


@askai.command()
def debug():
    """Toggle debugging ON/OFF."""
    configs.is_debug = not configs.is_debug
    text_formatter.cmd_print(f"`Debugging` is {'%GREEN%ON' if configs.is_debug else '%RED%OFF'}%NC%")


@askai.command()
def speak():
    """Toggle speaking ON/OFF."""
    configs.is_speak = not configs.is_speak
    text_formatter.cmd_print(f"`Speech-To-Text` is {'%GREEN%ON' if configs.is_speak else '%RED%OFF'}%NC%")
