import os

import click
from askai.core.askai_configs import configs
from askai.core.commander.commands.settings_cmd import SettingsCmd
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from hspylib.core.tools.commons import sysout

HELP_MSG = """
# AskAI Commander - HELP

> Commands:

```
  `/help`               : show this help message and exit.
  `/settings`           : list/get/set/reset settings.
  `/voices`             : list/set speech-to-text voice.
  `/tempo`              : list/set speech-to-text tempo.
  `/debug`              : toggle debugging ON/OFF.
  `/speak`              : toggle speaking ON/OFF.
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
@click.argument('key', default='')
@click.argument('value', default='')
def settings(operation: str, key: str | None = None, value: str | None = None) -> None:
    """Manage AskAI settings.
    :param operation The operation to manage settings.
    :param key The settings key to operate.
    :param value The settings value to be set.
    """
    match operation:
        case 'list':
            SettingsCmd.list(key)
        case 'get':
            SettingsCmd.get(key)
        case 'set':
            SettingsCmd.set(key, value)
        case 'reset':
            SettingsCmd.reset()
        case _:
            err = str(click.BadParameter(f"Invalid operation: '{operation}'"))
            text_formatter.cmd_print(f"%RED%{err}%NC%")


@askai.command()
@click.argument('operation', default='list')
@click.argument('name', default='onyx')
def voices(operation: str, name: str | None = None) -> None:
    """Set the Text-To-Speech voice."""
    all_voices = shared.engine.voices()
    str_voices = os.linesep.join([f"%YELLOW%{i}.%NC%  `{v}`" for i, v in enumerate(all_voices)])
    match operation:
        case 'list':
            sysout(str_voices)
        case 'set':
            if name in all_voices:
                SettingsCmd.set("openai.text.to.speech.voice", name)
                shared.engine.configs.tts_voice = name
                text_formatter.cmd_print(f"`Speech-To-Text` voice changed to %GREEN%{name}%NC%")
            else:
                text_formatter.cmd_print(f"%RED%Invalid voice: '{name}'%NC%")
        case _:
            err = str(click.BadParameter(f"Invalid operation: '{operation}'"))
            text_formatter.cmd_print(f"%RED%{err}%NC%")


@askai.command()
@click.argument('speed', type=click.INT, default=0)
def tempo(speed: int | None = None) -> None:
    """The Text-To-Speech tempo.
    :param speed The tempo to set.
    """
    if not speed:
        SettingsCmd.get("askai.text.to.speech.tempo")
    elif 1 <= speed <= 3:
        SettingsCmd.set("askai.text.to.speech.tempo", speed)
        configs.tempo = speed
        tempo_str: str = 'Normal' if speed == 1 else ('Fast' if speed == 2 else 'Ultra')
        text_formatter.cmd_print(f"`Speech-To-Text` **tempo** changed to %GREEN%{tempo_str} ({speed})%NC%")
    else:
        text_formatter.cmd_print(f"%RED%Invalid tempo value: '{speed}'. Please choose beteen [1..3].%NC%")


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
