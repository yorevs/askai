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
from os.path import dirname
from pathlib import Path
from string import Template

import click
from click import Command, Group
from hspylib.core.enums.charset import Charset

from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.commander.commands.cache_cmd import CacheCmd
from askai.core.commander.commands.history_cmd import HistoryCmd
from askai.core.commander.commands.settings_cmd import SettingsCmd
from askai.core.commander.commands.tts_stt_cmd import TtsSttCmd
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text

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


def _init_context(
    context_size: int = 1000,
    engine_name: str = "openai",
    model_name: str = "gpt-3.5-turbo",
) -> None:
    """Initialize AskAI context and startup components.
    :param context_size: The max size of e context window.
    :param engine_name: The name of the engine to initialize.
    :param model_name: The engine's model name to initialize.
    """
    if not (shared.engine and shared.context):
        shared.create_engine(engine_name=engine_name, model_name=model_name)
        shared.create_context(context_size)
        events.reply.subscribe(cb_event_handler=lambda ev: display_text(ev.args.message))


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
def cache(operation: str, name: str | None = None) -> None:
    """List/get/clear/cleanup AskAI cache.
    :param operation The operation to manage cache.
    :param name The settings key to operate.
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
@click.argument("dest_dir", default="")
@click.argument("playback", default="True")
def tts(text: str, dest_dir: str | None = None, playback: bool = True) -> None:
    """Convert a text to speech using the default AI engine.
    :param text: The text to be converted. If the text denotes a valid file, its contents will be used instead.
    :param dest_dir: The destination directory, where to save the converted file.
    :param playback: Whether to plat the audio file or not.
    """
    _init_context()
    if (text_path := Path(text)).exists and text_path.is_file():
        text: str = text_path.read_text(encoding=Charset.UTF_8.val)
    TtsSttCmd.tts(text.strip(), dirname(dest_dir), playback)
