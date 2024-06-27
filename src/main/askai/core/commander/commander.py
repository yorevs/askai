#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.commander
      @file: commander.py
   @created: Thu, 25 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import os
from string import Template

import click
from click import Command, Group

from askai.core.askai_configs import configs
from askai.core.commander.commands.cache_cmd import CacheCmd
from askai.core.commander.commands.history_cmd import HistoryCmd
from askai.core.commander.commands.settings_cmd import SettingsCmd
from askai.core.commander.commands.tts_stt_cmd import TtsSttCmd
from askai.core.support.text_formatter import text_formatter

COMMANDER_HELP_TPL = Template("""
# AskAI Commander - HELP

> Commands:

${commands}
---

> CLI-Input Key-Bindings:

| **Key**  | **Action**                    |
| -------- | ----------------------------- |
| *Ctrl+L* | **Push-To-Talk.**             |
| *Ctrl+R* | **Reset the input field.**    |
| *Ctrl+F* | **Forget the input history.** |
""")

__module__ = locals()


def commands() -> list[str]:
    """Return the list of all commander commands."""
    all_commands: set[str] = set()
    for name, obj in __module__.items():
        if obj and isinstance(obj, Command) and not isinstance(obj, Group):
            all_commands.add(f"/{name}")
    return sorted(all_commands, reverse=True)


def commander_help() -> str:
    """Return the commander help string."""
    helpstr: str = ""
    for cmd, obj in __module__.items():
        if obj and isinstance(obj, Command) and not isinstance(obj, Group):
            cmd_doc: str = f"{obj.__doc__.split(os.linesep, 1)[0]}**"
            helpstr += f"| /{'*' + cmd + '*':<8} | **{cmd_doc:<43} |\n"
    h_str: str = f"| {'**Command**':<9} | {'**Description**':<45} |\n"
    h_str += f"| {'-' * 9} | {'-' * 45} |\n"
    return COMMANDER_HELP_TPL.substitute(commands=f"{h_str}{helpstr}")


@click.group()
@click.pass_context
def ask_cli(_) -> None:
    """AskAI commands group."""
    pass


@ask_cli.command()
def help() -> None:
    """Show this help message and exit."""
    text_formatter.cmd_print(commander_help())


@ask_cli.command()
def debug() -> None:
    """Toggle debug mode ON/OFF."""
    configs.is_debug = not configs.is_debug
    text_formatter.cmd_print(f"`Debugging` is {'%GREEN%ON' if configs.is_debug else '%RED%OFF'}%NC%")


@ask_cli.command()
def speak() -> None:
    """Toggle speak mode ON/OFF."""
    configs.is_speak = not configs.is_speak
    text_formatter.cmd_print(f"`Speech-To-Text` is {'%GREEN%ON' if configs.is_speak else '%RED%OFF'}%NC%")


@ask_cli.command()
@click.argument("operation", default="list")
@click.argument("name", default="ALL")
def context(operation: str, name: str | None = None) -> None:
    """List/forget the current context window.
    :param operation The operation to manage contexts.
    :param name The context name.
    """
    match operation:
        case "forget":
            HistoryCmd.context_forget(name)
        case "list":
            HistoryCmd.context_list()


@ask_cli.command()
@click.argument("operation", default="list")
def history(operation: str) -> None:
    """List/forget the input history.
    :param operation The operation to manage history.
    """
    match operation:
        case "forget":
            HistoryCmd.history_forget()
        case "list":
            HistoryCmd.history_list()


@ask_cli.command()
@click.argument("operation", default="list")
@click.argument("name", default="")
def devices(operation: str, name: str | None = None) -> None:
    """List/set the audio input devices.
    :param operation The operation to manage devices.
    :param name The device name to set.
    """
    match operation:
        case "list":
            TtsSttCmd.device_list()
        case "set":
            TtsSttCmd.device_set(name)
        case _:
            err = str(click.BadParameter(f"Invalid settings operation: '{operation}'"))
            text_formatter.cmd_print(f"%RED%{err}%NC%")


@ask_cli.command()
@click.argument("operation", default="list")
@click.argument("name", default="")
@click.argument("value", default="")
def settings(operation: str, name: str | None = None, value: str | None = None) -> None:
    """List/get/set/reset AskAI settings.
    :param operation The operation to manage settings.
    :param name The settings key to operate.
    :param value The settings value to be set.
    """
    match operation:
        case "list":
            SettingsCmd.list(name)
        case "get":
            SettingsCmd.get(name)
        case "set":
            SettingsCmd.set(name, value)
        case "reset":
            SettingsCmd.reset()
        case _:
            err = str(click.BadParameter(f"Invalid settings operation: '{operation}'"))
            text_formatter.cmd_print(f"%RED%{err}%NC%")




@ask_cli.command()
@click.argument("operation", default="list")
@click.argument("name", default="")
@click.argument("value", default="")
def cache(operation: str, name: str | None = None, value: str | None = None) -> None:
    """List/get/clear AskAI cache.
    :param operation The operation to manage cache.
    :param name The settings key to operate.
    :param value The settings value to be set.
    """
    match operation:
        case "list":
            CacheCmd.list()
        case "get":
            CacheCmd.get(name)
        case "clear":
            CacheCmd.clear(name)
        case _:
            err = str(click.BadParameter(f"Invalid cache operation: '{operation}'"))
            text_formatter.cmd_print(f"%RED%{err}%NC%")


@ask_cli.command()
@click.argument("speed", type=click.INT, default=1)
def tempo(speed: int | None = None) -> None:
    """List/set speech-to-text tempo.
    :param speed The tempo to set.
    """
    TtsSttCmd.tempo(speed)


@ask_cli.command()
@click.argument("operation", default="list")
@click.argument("name", default="onyx")
def voices(operation: str, name: str | int | None = None) -> None:
    """List/set/play speech-to-text voices.
    :param operation The operation to manage voices.
    :param name The voice name.
    """
    match operation:
        case "list":
            TtsSttCmd.voice_list()
        case "set":
            TtsSttCmd.voice_set(name)
        case "play":
            TtsSttCmd.voice_play(name)
        case _:
            err = str(click.BadParameter(f"Invalid voices operation: '{operation}'"))
            text_formatter.cmd_print(f"%RED%{err}%NC%")


@ask_cli.command()
@click.argument("text")
@click.argument("dest", default="")
def tts(text: str, dest: str | None = None) -> None:
    TtsSttCmd.tts(text, dest)


if __name__ == '__main__':
    ask_cli(['tts', 'TEXTO'], standalone_mode=False)
