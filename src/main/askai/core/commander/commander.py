#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.commander
      @file: commander.py
   @created: Thu, 25 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import os
from functools import partial
from os.path import dirname
from pathlib import Path
from string import Template

import click
from click import Command, Group
from clitt.core.term.cursor import cursor
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import sysout, to_bool
from hspylib.modules.eventbus.event import Event

from askai.core.askai_configs import configs
from askai.core.askai_events import events, AskAiEvents, ASKAI_BUS_NAME, REPLY_EVENT, REPLY_ERROR_EVENT
from askai.core.commander.commands.cache_cmd import CacheCmd
from askai.core.commander.commands.camera_cmd import CameraCmd
from askai.core.commander.commands.general_cmd import GeneralCmd
from askai.core.commander.commands.history_cmd import HistoryCmd
from askai.core.commander.commands.settings_cmd import SettingsCmd
from askai.core.commander.commands.tts_stt_cmd import TtsSttCmd
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text
from askai.language.language import Language, AnyLocale

COMMANDER_HELP_TPL = Template(
    """
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
"""
)

RE_ASKAI_CMD: str = r"^(?<!\\)/(\w+)( (.*))*$"

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


def _init_context(context_size: int = 1000, engine_name: str = "openai", model_name: str = "gpt-4o-mini") -> None:
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
def ask_commander(_) -> None:
    """AskAI commands group."""

    def _reply_event(ev: Event, error: bool = False) -> None:
        if message := ev.args.message:
            if error:
                text_formatter.cmd_print(f"%RED%{message}!%NC%")
            else:
                if ev.args.erase_last:
                    cursor.erase_line()
                display_text(message)

    askai_bus = AskAiEvents.bus(ASKAI_BUS_NAME)
    askai_bus.subscribe(REPLY_EVENT, _reply_event)
    askai_bus.subscribe(REPLY_ERROR_EVENT, partial(_reply_event, error=True))


@ask_commander.command()
def help() -> None:
    """Show this help message and exit."""
    text_formatter.cmd_print(commander_help())


@ask_commander.command()
def debug() -> None:
    """Toggle debug mode ON/OFF."""
    configs.is_debug = not configs.is_debug
    text_formatter.cmd_print(f"`Debugging` is {'%GREEN%ON' if configs.is_debug else '%RED%OFF'}%NC%")


@ask_commander.command()
def speak() -> None:
    """Toggle speak mode ON/OFF."""
    configs.is_speak = not configs.is_speak
    text_formatter.cmd_print(f"`Speech-To-Text` is {'%GREEN%ON' if configs.is_speak else '%RED%OFF'}%NC%")


@ask_commander.command()
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


@ask_commander.command()
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


@ask_commander.command()
@click.argument("name", default="LAST_REPLY")
def copy(name: str) -> None:
    """Copy a context entry to the clipboard
    :param name: The context name.
    """
    HistoryCmd.context_copy(name)


@ask_commander.command()
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
            text_formatter.cmd_print(f"Error: {err}")


@ask_commander.command()
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
            text_formatter.cmd_print(f"Error: {err}")


@ask_commander.command()
@click.argument("operation", default="list")
@click.argument("args", nargs=-1)
def cache(operation: str, args: tuple[str, ...]) -> None:
    """List/get/clear/files AskAI TTL cache and files.
    :param operation The operation to manage cache.
    :param args The operation arguments operate.
    """
    match operation:
        case "list":
            CacheCmd.list()
        case "get":
            if not args:
                err: str = str(click.MissingParameter(f"Argument 'name' is required. Usage /cache get \\<name\\>"))
                text_formatter.cmd_print(f"Error: {err}")
            else:
                set(map(sysout, map(CacheCmd.get, args)))
        case "clear":
            if args and (invalid := next((a for a in args if not isinstance(a, str | int)), None)):
                err: str = str(click.BadParameter(f"Invalid argument: '{invalid}'"))
                text_formatter.cmd_print(f"Error: {err}")
            elif args:
                set(map(CacheCmd.clear, args))
            else:
                CacheCmd.clear()
        case "files":
            CacheCmd.files("cleanup" in args, *args)
        case "enable":
            if not args:
                err: str = str(click.MissingParameter(f"Arguments missing. Usage /cache enable \\<0|1\\>"))
                text_formatter.cmd_print(f"Error: {err}")
            else:
                configs.is_cache = to_bool(args[0])
                text_formatter.cmd_print(f"Caching has been *{'en' if configs.is_cache else 'dis'}abled* !")
        case "ttl":
            if not args:
                text_formatter.cmd_print(f"Cache TTL is set to *{configs.ttl} minutes* !")
            elif not args[0].isdigit():
                err: str = str(click.MissingParameter(f"Argument 'minutes' is invalid. Usage /cache ttl \\<minutes\\>"))
                text_formatter.cmd_print(f"Error: {err}")
            else:
                configs.ttl = int(args[0])
                text_formatter.cmd_print(f"Cache TTL was set to *{args[0]} minutes* !")
        case _:
            err: str = str(click.BadParameter(f"Invalid cache operation: '{operation}'"))
            text_formatter.cmd_print(f"Error: {err}")


@ask_commander.command()
@click.argument("speed", type=click.INT, default=1)
def tempo(speed: int | None = None) -> None:
    """List/set speech-to-text tempo.
    :param speed The tempo to set.
    """
    TtsSttCmd.tempo(speed)


@ask_commander.command()
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


@ask_commander.command()
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


@ask_commander.command()
@click.argument("folder")
@click.argument("glob", default="**/*")
def summarize(folder: str, glob: str) -> None:
    """Generate a summarization of the folder contents.
    :param folder: The base folder of the summarization.
    :param glob: The glob pattern or file of the summarization.
    """
    _init_context()
    GeneralCmd.summarize(folder, glob)


@ask_commander.command()
@click.argument("locale_str", default="")
def idiom(locale_str: str) -> None:
    """Set the application language.
    :param locale_str: The locale string.
    """
    GeneralCmd.idiom(locale_str)


@ask_commander.command()
def info() -> None:
    """Display some useful application information."""
    if os.getenv("ASKAI_APP"):
        GeneralCmd.app_info()
    else:
        text_formatter.cmd_print("No information available (offline)!")


@ask_commander.command()
@click.argument("from_locale_str")
@click.argument("to_locale_str")
@click.argument("texts", nargs=-1)
def translate(from_locale_str: AnyLocale, to_locale_str: AnyLocale, texts: tuple[str, ...]) -> None:
    """Translate a text from the source language to the target language.
    :param from_locale_str: The source idiom.
    :param to_locale_str: The target idiom.
    :param texts: The texts to be translated.
    """
    GeneralCmd.translate(
        Language.of_locale(from_locale_str),
        Language.of_locale(to_locale_str),
        ' '.join(texts)
    )


@ask_commander.command()
@click.argument("operation", default="capture")
@click.argument("args", nargs=-1)
def camera(operation: str, args: tuple[str, ...]) -> None:
    """Take photos, import images or identify a person using hte WebCam.
    :param operation: the camera operation.
    :param args The operation arguments operate.
    """
    match operation:
        case "capture" | "photo":
            CameraCmd.capture(*args)
        case "identify" | "id":
            CameraCmd.identify(*args)
        case "import":
            CameraCmd.import_images(*args)
        case _:
            err = str(click.BadParameter(f"Invalid camera operation: '{operation}'"))
            text_formatter.cmd_print(f"%RED%{err}%NC%")


if __name__ == "__main__":
    pass
    # shared.create_context(1000)
    # shared.context.push("LAST_REPLY", "This is the last reply!")
    # shared.context.push("LAST_REPLY", "This is the another last reply!")
    # ask_commander(["copy"], standalone_mode=False)
    # print(pyperclip.paste())
    # ask_commander(["info"], standalone_mode=False)
    # ask_commander(['idiom'], standalone_mode=False)
    # ask_commander(['idiom', 'pt_BR.iso8859-1'], standalone_mode=False)
    # ask_commander(['idiom'], standalone_mode=False)
    # cache_service.cache.save_reply('log', "Log message is a big reply that will be wrapped into")
    # cache_service.cache.save_reply('audio', "Audio message")
    # ask_commander(['cache'], standalone_mode=False)
    # ask_commander(['cache', 'get', 'log', 'audio'], standalone_mode=False)
    # ask_commander(['cache', 'clear'], standalone_mode=False)
    # ask_commander(['cache', 'clear', 'log', 'audio'], standalone_mode=False)
    # ask_commander(['cache', 'files'], standalone_mode=False)
    # ask_commander(['cache', 'files', 'cleanup', 'askai'], standalone_mode=False)
    # ask_commander(['cache', 'files', 'cleanup', 'recordings'], standalone_mode=False)
    # ask_commander(['camera'], standalone_mode=False)
    # ask_commander(['camera', 'id', 'True'], standalone_mode=False)
    # ask_commander(['camera', 'import', '/tmp/*.jpeg'], standalone_mode=False)
    # ask_commander(['camera', 'import', '/Users/hjunior/Downloads'], standalone_mode=False)
    ask_commander(['translate', 'pt_BR', 'fr_FR', "Olá eu sou o Hugo desenvolvedor pleno!"], standalone_mode=False)
