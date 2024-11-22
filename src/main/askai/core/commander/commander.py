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
from askai.core.askai_configs import configs
from askai.core.askai_events import ASKAI_BUS_NAME, AskAiEvents, events, REPLY_EVENT
from askai.core.commander.commands.cache_cmd import CacheCmd
from askai.core.commander.commands.camera_cmd import CameraCmd
from askai.core.commander.commands.general_cmd import GeneralCmd
from askai.core.commander.commands.history_cmd import HistoryCmd
from askai.core.commander.commands.settings_cmd import SettingsCmd
from askai.core.commander.commands.tts_stt_cmd import TtsSttCmd
from askai.core.component.rag_provider import RAGProvider
from askai.core.enums.router_mode import RouterMode
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text
from askai.language.language import AnyLocale, Language
from click import Command, Group
from clitt.core.term.cursor import cursor
from functools import lru_cache
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import sysout, to_bool
from hspylib.modules.eventbus.event import Event
from os.path import dirname
from pathlib import Path
from string import Template
from textwrap import dedent

import click
import os
import re

COMMANDER_HELP_TPL = Template(
    dedent(
        """\
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

    >   To get help about a specific command type: '/help \\<command\\>'
    """
    )
)

COMMANDER_HELP_CMD_TPL = Template(
    dedent(
        """\
    # AskAI Commander - HELP
    ```
    %CYAN%Command: %ORANGE%${command}%NC%

        ${docstr}

    %CYAN%Usage:\t%WHITE%/${usage}
    ```
    """
    )
)

RE_ASKAI_CMD: str = r"^(?<!\\)/(\w+)( (.*))*$"

__module__ = locals()


@lru_cache
def commands() -> list[str]:
    """Return the list of all available commander commands.
    :return: A list of strings representing the available commands.
    """
    all_commands: set[str] = set()
    for name, obj in __module__.items():
        if obj and isinstance(obj, Command) and not isinstance(obj, Group):
            all_commands.add(f"/{name}")
    return sorted(all_commands, reverse=True)


@lru_cache
def commander_help(command: str | None = None) -> str:
    """Return the help string for the specified commander command.
    :param command: The command for which to retrieve help.
    :return: A string containing the help information for the specified command.
    """
    if (command in __module__) and (cmd := __module__[command]):
        return _format_help(cmd)
    else:
        help_str: str = ""
        for cmd, obj in __module__.items():
            if obj and isinstance(obj, Command) and not isinstance(obj, Group):
                cmd_doc: str = f"{obj.__doc__.split(os.linesep, 1)[0]}**"
                help_str += f"| /{'*' + cmd + '*':<8} | **{cmd_doc:<43} |\n"
        h_str: str = f"| {'**Command**':<9} | {'**Description**':<45} |\n"
        h_str += f"| {'-' * 9} | {'-' * 45} |\n"
        return COMMANDER_HELP_TPL.substitute(commands=f"{h_str}{help_str}")


def is_command(string: str) -> bool:
    """Check if the given string is a command.
    :param string: The string to check.
    :return: True if the string is a command, False otherwise.
    """
    return string.startswith("/") and string in commands()


def _format_help(command: Command) -> str:
    """Return a formatted help string for the given command.
    :param command: The command for which the help string will be formatted.
    :return: A formatted string containing the help information for the specified command.
    """
    docstr: str = ""
    re_flags = re.MULTILINE | re.IGNORECASE
    splits: list[str] = re.split(os.linesep, command.__doc__, flags=re_flags)
    for i, arg in enumerate(splits):
        if mat := re.match(r":\w+\s+(\w+):\s+(.+)", arg.strip()):
            docstr += f"\n\t\t- %BLUE%{mat.group(1).casefold():<15}%WHITE%\t: {mat.group(2).title()}"
        elif arg.strip():
            docstr += f"{arg}\n\n%CYAN%Arguments:%NC%\n"
    usage_str: str = f"{command.name} {' '.join(['<' + p.name + '>' for p in command.params])}"

    return COMMANDER_HELP_CMD_TPL.substitute(command=command.name.title(), docstr=docstr, usage=usage_str)


def _init_context(context_size: int = 1000, engine_name: str = "openai", model_name: str = "gpt-4o-mini") -> None:
    """Initialize the AskAI context and startup components.
    :param context_size: The maximum size of the context window (default is 1000).
    :param engine_name: The name of the engine to initialize (default is "openai").
    :param model_name: The model name of the engine to initialize (default is "gpt-3.5-turbo").
    """

    def _reply_event(ev: Event, error: bool = False) -> None:
        """Callback for handling the reply event.
        :param ev: The event object representing the reply event.
        :param error: Indicates whether the reply contains an error (default is False).
        """
        if message := ev.args.message:
            if error:
                text_formatter.commander_print(f"%RED%{message}!%NC%")
            else:
                if ev.args.erase_last:
                    cursor.erase_line()
                display_text(message)

    if shared.engine is None and shared.context is None:
        shared.create_engine(engine_name=engine_name, model_name=model_name, mode=RouterMode.default())
        shared.create_context(context_size)
        askai_bus = AskAiEvents.bus(ASKAI_BUS_NAME)
        askai_bus.subscribe(REPLY_EVENT, _reply_event)


@click.group()
@click.pass_context
def ask_commander(_) -> None:
    """AskAI commands group. This function serves as the entry point for the AskAI command-line interface (CLI)
    commands, grouping related commands together.
    """
    _init_context()


@ask_commander.command()
@click.argument("command", default="")
def help(command: str | None) -> None:
    """Display the help message for the specified command and exit. If no command is provided, it displays the general
    help message.
    :param command: The command to retrieve help for (optional).
    """
    display_text(commander_help(command.replace("/", "")))


@ask_commander.command()
def assistive() -> None:
    """Toggle assistive mode ON/OFF."""
    configs.is_assistive = not configs.is_assistive
    text_formatter.commander_print(
        f"`Assistive responses` is {'%GREEN%ON' if configs.is_assistive else '%RED%OFF'}%NC%"
    )


@ask_commander.command()
def debug() -> None:
    """Toggle debug mode ON/OFF."""
    configs.is_debug = not configs.is_debug
    text_formatter.commander_print(f"`Debugging` is {'%GREEN%ON' if configs.is_debug else '%RED%OFF'}%NC%")


@ask_commander.command()
def speak() -> None:
    """Toggle speak mode ON/OFF."""
    configs.is_speak = not configs.is_speak
    text_formatter.commander_print(f"`Speech-To-Text` is {'%GREEN%ON' if configs.is_speak else '%RED%OFF'}%NC%")


@ask_commander.command()
@click.argument("operation", default="list")
@click.argument("name", default="ALL")
def context(operation: str, name: str | None = None) -> None:
    """Manage the current chat context window.
    :param operation: The operation to perform on contexts. Options: [list | forget].
    :param name: The name of the context to target (default is "ALL").
    """
    match operation.casefold():
        case "list":
            HistoryCmd.context_list()
        case "forget":
            HistoryCmd.context_forget(name)
        case _:
            err = str(click.BadParameter(f"Invalid settings operation: '{operation}'"))
            text_formatter.commander_print(f"Error: {err}")


@ask_commander.command()
@click.argument("operation", default="list")
def history(operation: str) -> None:
    """Manages the current input history.
    :param operation: The operation to perform on contexts. Options: [list|forget].
    """
    match operation.casefold():
        case "list":
            HistoryCmd.history_list()
        case "forget":
            HistoryCmd.history_forget()
        case _:
            err = str(click.BadParameter(f"Invalid settings operation: '{operation}'"))
            text_formatter.commander_print(f"Error: {err}")


@ask_commander.command()
@click.argument("name", default="LAST_REPLY")
def copy(name: str) -> None:
    """Copy the specified context entry to the clipboard.
    :param name: The name of the context entry to copy.
    """
    HistoryCmd.context_copy(name)


@ask_commander.command()
@click.argument("operation", default="list")
@click.argument("name", default="")
def devices(operation: str, name: str | None = None) -> None:
    """Manages the audio input devices.
    :param operation: Specifies the device operation. Options: [list|set].
    :param name: The target device name for setting.
    """
    match operation.casefold():
        case "list":
            TtsSttCmd.device_list()
        case "set":
            TtsSttCmd.device_set(name)
        case _:
            err = str(click.BadParameter(f"Invalid settings operation: '{operation}'"))
            text_formatter.commander_print(f"Error: {err}")


@ask_commander.command()
@click.argument("operation", default="list")
@click.argument("name", default="")
@click.argument("value", default="")
def settings(operation: str, name: str | None = None, value: str | None = None) -> None:
    """Handles modifications to AskAI settings.
    :param operation: The action to perform on settings. Options: [list|get|set|reset]
    :param name: The key for the setting to modify.
    :param value: The new value for the specified setting.
    """
    match operation.casefold():
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
            text_formatter.commander_print(f"Error: {err}")


@ask_commander.command()
@click.argument("operation", default="list")
@click.argument("args", nargs=-1)
def cache(operation: str, args: tuple[str, ...]) -> None:
    """Manages AskAI TTL-cache management and associated files.
    :param operation: Specifies the cache operation. Options: [list|get|clear|files|enable|ttl]
    :param args: Arguments relevant to the chosen operation.
    """
    match operation.casefold():
        case "list":
            CacheCmd.list()
        case "get":
            if not args:
                err: str = str(click.MissingParameter(f"Argument 'name' is required. Usage /cache get \\<name\\>"))
                text_formatter.commander_print(f"Error: {err}")
            else:
                set(map(sysout, map(CacheCmd.get, args)))
        case "clear":
            if args and (invalid := next((a for a in args if not isinstance(a, str | int)), None)):
                err: str = str(click.BadParameter(f"Invalid argument: '{invalid}'"))
                text_formatter.commander_print(f"Error: {err}")
            elif args:
                set(map(CacheCmd.clear, args))
            else:
                CacheCmd.clear()
        case "files":
            CacheCmd.files("cleanup" in args, *args)
        case "enable":
            if not args:
                err: str = str(click.MissingParameter(f"Arguments missing. Usage /cache enable \\<0|1\\>"))
                text_formatter.commander_print(f"Error: {err}")
            else:
                configs.is_cache = to_bool(args[0])
                text_formatter.commander_print(f"Caching has been *{'en' if configs.is_cache else 'dis'}abled* !")
        case "ttl":
            if not args:
                text_formatter.commander_print(f"Cache TTL is set to *{configs.ttl} minutes* !")
            elif not args[0].isdigit():
                err: str = str(click.MissingParameter(f"Argument 'minutes' is invalid. Usage /cache ttl \\<minutes\\>"))
                text_formatter.commander_print(f"Error: {err}")
            else:
                configs.ttl = int(args[0])
                text_formatter.commander_print(f"Cache TTL was set to *{args[0]} minutes* !")
        case _:
            text_formatter.commander_print(f"Cache is *{'en' if configs.is_rag else 'dis'}abled* !")


@ask_commander.command()
@click.argument("speed", type=click.INT, default=1)
def tempo(speed: int | None = None) -> None:
    """Manages the speech-to-text tempo.
    :param speed: Desired speech tempo setting. Options: [list|get]
    """
    TtsSttCmd.tempo(speed)


@ask_commander.command()
@click.argument("operation", default="list")
@click.argument("name", default="onyx")
def voices(operation: str, name: str | int | None = None) -> None:
    """Manages speech-to-text voice operations.
    :param operation: The action to perform on voices. Options: [list/set/play]
    :param name: The voice name.
    """
    match operation.casefold():
        case "list":
            TtsSttCmd.voice_list()
        case "set":
            TtsSttCmd.voice_set(name)
        case "play":
            TtsSttCmd.voice_play(name)
        case _:
            err = str(click.BadParameter(f"Invalid voices operation: '{operation}'"))
            text_formatter.commander_print(f"%RED%{err}%NC%")


@ask_commander.command()
@click.argument("text")
@click.argument("dest_dir", default="")
@click.argument("playback", default="True")
def tts(text: str, dest_dir: str | None = None, playback: bool = True) -> None:
    """Convert text to speech using the default AI engine.
    :param text: The text to convert. If text represents a valid file, its contents will be used instead.
    :param dest_dir: The directory where the converted audio file will be saved.
    :param playback: Whether to play the audio file after conversion.
    """
    if (text_path := Path(text)).exists and text_path.is_file():
        text: str = text_path.read_text(encoding=Charset.UTF_8.val)
    TtsSttCmd.tts(text.strip(), dirname(dest_dir), playback)


@ask_commander.command()
@click.argument("folder")
@click.argument("glob", default="**/*")
def summarize(folder: str, glob: str) -> None:
    """Create a summary of the folder's contents.
    :param folder: The root directory for the summary.
    :param glob: The file pattern or path to summarize.
    """
    GeneralCmd.summarize(folder, glob)


@ask_commander.command()
@click.argument("locale_str", default="")
def idiom(locale_str: str) -> None:
    """Set the application's language preference.
    :param locale_str: The locale identifier, e.g., 'pt_BR'.
    """
    GeneralCmd.idiom(locale_str)


@ask_commander.command()
def info() -> None:
    """Display key information about the running application."""
    if os.getenv("ASKAI_APP"):
        GeneralCmd.app_info()
    else:
        text_formatter.commander_print("No information available (offline)!")


@ask_commander.command()
@click.argument("from_locale_str")
@click.argument("to_locale_str")
@click.argument("texts", nargs=-1)
def translate(from_locale_str: AnyLocale, to_locale_str: AnyLocale, texts: tuple[str, ...]) -> None:
    """Translate text from the source language to the target language.
    :param from_locale_str: The source locale identifier, e.g., 'pt_BR'.
    :param to_locale_str: The target locale identifier, e.g., 'en_US'.
    :param texts: The list of texts to translate.
    """
    GeneralCmd.translate(Language.of_locale(from_locale_str), Language.of_locale(to_locale_str), " ".join(texts))


@ask_commander.command()
@click.argument("operation", default="capture")
@click.argument("args", nargs=-1)
def camera(operation: str, args: tuple[str, ...]) -> None:
    """Take photos, import images, or identify a person using the WebCam.
    :param operation: The camera operation to perform. Options: [capture|identify|import]
    :param args: The arguments required for the operation.
    """
    match operation.casefold():
        case "capture" | "photo":
            CameraCmd.capture(*args)
        case "identify" | "id":
            CameraCmd.identify(*args)
        case "import":
            CameraCmd.import_images(*args)
        case _:
            err = str(click.BadParameter(f"Invalid camera operation: '{operation}'"))
            text_formatter.commander_print(f"%RED%{err}%NC%")


@ask_commander.command()
@click.argument("router_mode", default="")
def mode(router_mode: str) -> None:
    """Change the AskAI routing mode.
    :param router_mode: The routing mode. Options: [rag|chat|splitter]
    """
    if not router_mode:
        text_formatter.commander_print(f"Available routing modes: **[rag|chat|splitter]**. Current: `{shared.mode}`")
    else:
        match router_mode.casefold():
            case "rag":
                events.mode_changed.emit(mode="RAG")
            case "chat":
                events.mode_changed.emit(mode="CHAT")
            case "splitter":
                events.mode_changed.emit(mode="SPLITTER")
            case _:
                events.mode_changed.emit(mode="DEFAULT")


@ask_commander.command()
@click.argument("operation", default="")
@click.argument("args", nargs=-1)
def rag(operation: str, args: tuple[str, ...]) -> None:
    """Manages AskAI RAG features.
    :param operation: Specifies the rag operation. Options: [add|enable]
    :param args: Arguments relevant to the chosen operation.
    """
    match operation.casefold():
        case "add":
            if not args:
                err: str = str(click.MissingParameter(f"Arguments missing. Usage /rag add \\<folder\\>"))
                text_formatter.commander_print(f"Error: {err}")
            else:
                folder: Path = Path(args[0])
                if not folder.exists():
                    text_formatter.commander_print(f"Error: Could not find folder: '{folder}'")
                else:
                    if RAGProvider.copy_rag(folder):
                        text_formatter.commander_print(f"RAG folder '{folder}' has been *added* to rag directory !")
                    else:
                        text_formatter.commander_print(f"Error: Failed to add RAG folder: '{folder}' !")

        case "enable":
            if not args:
                err: str = str(click.MissingParameter(f"Arguments missing. Usage /rag enable \\<0|1\\>"))
                text_formatter.commander_print(f"Error: {err}")
            else:
                configs.is_rag = to_bool(args[0])
                text_formatter.commander_print(f"RAG has been *{'en' if configs.is_rag else 'dis'}abled* !")
        case _:
            text_formatter.commander_print(f"RAG is *{'en' if configs.is_rag else 'dis'}abled* !")
