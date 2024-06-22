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

import click

from askai.core.askai_configs import configs
from askai.core.commander.commands.history_cmd import HistoryCmd
from askai.core.commander.commands.settings_cmd import SettingsCmd
from askai.core.commander.commands.tts_stt_cmd import TtsSttCmd
from askai.core.support.text_formatter import text_formatter

COMMANDER_HELP = """
# AskAI Commander - HELP

> Commands:

|  Command  | Description                                   |
| --------- | --------------------------------------------- |
| /help     | **Show this help message and exit.**          |
| /debug    | **Toggle debugging ON/OFF.**                  |
| /speak    | **Toggle speaking ON/OFF.**                   |
| /context  | **List/forget the current context window.**   |
| /devices  | **List/set the audio input devices.**         |
| /settings | **List/get/set/reset settings.**              |
| /tempo    | **List/set speech-to-text tempo.**            |
| /voices   | **List/set/play speech-to-text voices.**      |

---

> Input Key-Bindings:

| Key      | Action                         |
| -------- | ------------------------------ |
| Ctrl+L   | **Push-To-Talk.**              |
| Ctrl+R   | **Reset the input field.**     |
| Ctrl+F   | **Forget the input history.**  |
"""


@click.group()
@click.pass_context
def ask_cli(ctx) -> None:
    """TODO"""
    pass


@ask_cli.command()
def help() -> None:
    """Display this help and exit."""
    text_formatter.cmd_print(COMMANDER_HELP)


@ask_cli.command()
@click.argument("operation", default="list")
@click.argument("name", default="")
@click.argument("value", default="")
def settings(operation: str, name: str | None = None, value: str | None = None) -> None:
    """Manage AskAI settings.
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
def devices(operation: str, name: str | None = None) -> None:
    """Manage the Audio Input devices.
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
@click.argument("name", default="onyx")
def voices(operation: str, name: str | int | None = None) -> None:
    """Manage the Text-To-Speech voices.
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
@click.argument("speed", type=click.INT, default=1)
def tempo(speed: int | None = None) -> None:
    """Adjust the Text-To-Speech tempo.
    :param speed The tempo to set.
    """
    TtsSttCmd.tempo(speed)


@ask_cli.command()
def debug() -> None:
    """Toggle debugging ON/OFF."""
    configs.is_debug = not configs.is_debug
    text_formatter.cmd_print(f"`Debugging` is {'%GREEN%ON' if configs.is_debug else '%RED%OFF'}%NC%")


@ask_cli.command()
def speak() -> None:
    """Toggle speaking ON/OFF."""
    configs.is_speak = not configs.is_speak
    text_formatter.cmd_print(f"`Speech-To-Text` is {'%GREEN%ON' if configs.is_speak else '%RED%OFF'}%NC%")


@ask_cli.command()
@click.argument("operation", default="list")
@click.argument("name", default="ALL")
def context(operation: str, name: str | int | None = None) -> None:
    """Manage the chat context.
    :param operation The operation to manage contexts.
    :param name The context name.
    """
    match operation:
        case "forget":
            HistoryCmd.forget(name)
        case "list":
            HistoryCmd.list()
