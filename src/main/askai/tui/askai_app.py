#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.tui.askai_app
      @file: askai_app.py
   @created: Mon, 29 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import logging as log
import os
import re
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import nltk
from click import UsageError
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import is_debugging, file_is_not_empty
from hspylib.core.tools.text_tools import elide_text, ensure_endswith, strip_escapes
from hspylib.core.zoned_datetime import DATE_FORMAT, now, TIME_FORMAT
from hspylib.modules.application.version import Version
from hspylib.modules.eventbus.event import Event
from openai import RateLimitError
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Footer, Input, MarkdownViewer

from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.askai_events import *
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.askai_settings import settings
from askai.core.commander.commander import ask_cli, commander_help
from askai.core.component.audio_player import player
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.core.component.recorder import recorder
from askai.core.component.scheduler import scheduler
from askai.core.engine.ai_engine import AIEngine
from askai.core.enums.router_mode import RouterMode
from askai.core.features.router.ai_processor import AIProcessor
from askai.core.support.chat_context import ChatContext
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.exception.exceptions import *
from askai.tui.app_header import Header
from askai.tui.app_icons import AppIcons
from askai.tui.app_suggester import InputSuggester
from askai.tui.app_widgets import AppHelp, AppInfo, AppSettings, Splash

SOURCE_DIR: Path = classpath.source_path()

RESOURCE_DIR: Path = classpath.resource_path()


class AskAiApp(App[None]):
    """The AskAI Textual application."""

    APP_TITLE: str = f"AskAI v{Version.load(load_dir=classpath.source_path())}"

    CSS_PATH = f"{RESOURCE_DIR}/askai.tcss"

    # fmt: off
    BINDINGS = [
        ("q", "quit", msg.translate(" Quit")),
        ("c", "clear", msg.translate(" Clear")),
        ("d", "debugging", msg.translate(" Debugging")),
        ("s", "speaking", msg.translate(" Speaking")),
        ("ctrl+l", "ptt", msg.translate(" Push-to-Talk")),
    ]
    # fmt: on

    ENABLE_COMMAND_PALETTE = False

    SPLASH_IMAGE: str = classpath.get_resource("splash.txt").read_text(encoding=Charset.UTF_8.val)

    RE_ASKAI_CMD: str = r"^(?<!\\)/(\w+)( (.*))*$"

    def __init__(self, quiet: bool, debug: bool, cacheable: bool, tempo: int, engine_name: str, model_name: str):
        super().__init__()
        self._session_id = now("%Y%m%d")[:8]
        self._question: str | None = None
        self._engine: AIEngine = shared.create_engine(engine_name, model_name)
        self._context: ChatContext = shared.create_context(self._engine.ai_token_limit())
        self._mode: RouterMode = RouterMode.default()
        self._console_path = Path(f"{CACHE_DIR}/askai-{self.session_id}.md")
        self._re_render = True
        self._display_buffer = list()
        if not self._console_path.exists():
            self._console_path.touch()

        # Save setting configs from program arguments to remember later.
        configs.is_interactive = True
        configs.is_speak = not quiet
        configs.is_debug = is_debugging() or debug
        configs.is_cache = cacheable
        configs.tempo = tempo
        configs.engine = engine_name
        configs.model = model_name
        self._startup()

    def __str__(self) -> str:
        device_info = f"{recorder.input_device[1]}" if recorder.input_device else ""
        device_info += f", AUTO-SWAP {'ON' if recorder.is_auto_swap else 'OFF'}"
        speak_info = str(configs.tempo) + " @" + shared.engine.configs.tts_voice
        cur_dir = elide_text(str(Path(os.getcwd()).absolute()), 67, "…")
        return (
            "\n"
            f"   Language: {configs.language}\n"
            f"     Engine: {self.engine}\n"
            f"        Dir: {cur_dir}\n"
            f"         OS: {prompt.os_type.title()} - {prompt.shell.title()} \n"
            f"{'-' * 80}\n"
            f" Microphone: {device_info or 'Undetected'}\n"
            f"  Debugging: {'ON' if configs.is_debug else 'OFF'}\n"
            f"   Speaking: {'ON, tempo: ' + speak_info if configs.is_speak else 'OFF'}\n"
            f"    Caching: {'ON, TTL: ' + str(configs.ttl) if configs.is_cache else 'OFF'} "
            "\n"
        )

    @property
    def engine(self) -> AIEngine:
        return self._engine

    @property
    def context(self) -> ChatContext:
        return self._context

    @property
    def mode(self) -> RouterMode:
        return self._mode

    @property
    def question(self) -> str:
        return self._question

    @property
    def nickname(self) -> str:
        return f"*  Taius*"

    @property
    def username(self) -> str:
        return f"**  {prompt.user.title()}**"

    @property
    def md_console(self) -> MarkdownViewer:
        """Get the MarkdownViewer widget."""
        return self.query_one(MarkdownViewer)

    @property
    def info(self) -> AppInfo:
        """Get the AppInfo widget."""
        return self.query_one(AppInfo)

    @property
    def help(self) -> AppHelp:
        """Get the AppHelp widget."""
        return self.query_one(AppHelp)

    @property
    def settings(self) -> AppSettings:
        """Get the AppSettings widget."""
        return self.query_one(AppSettings)

    @property
    def splash(self) -> Splash:
        """Get the Splash widget."""
        return self.query_one(Splash)

    @property
    def line_input(self) -> Input:
        """Get the Input widget."""
        return self.query_one(Input)

    @property
    def suggester(self) -> Optional[InputSuggester]:
        """Get the Input Suggester."""
        return self.line_input.suggester

    @property
    def header(self) -> Header:
        """Get the Input widget."""
        return self.query_one(Header)

    @property
    def footer(self) -> Footer:
        """Get the Input widget."""
        return self.query_one(Footer)

    @property
    def session_id(self) -> str:
        """Get the Session id."""
        return self._session_id

    @property
    def app_settings(self) -> list[tuple[str, ...]]:
        all_settings = [("UUID", "Setting", "Value")]
        for s in settings.settings.search():
            r: tuple[str, ...] = str(s.identity["uuid"]), str(s.name), str(s.value)
            all_settings.append(r)
        return all_settings

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        suggester = InputSuggester(case_sensitive=False)
        footer = Footer()
        footer.upper_case_keys = True
        footer.ctrl_to_caret = True
        yield Header()
        with ScrollableContainer():
            yield AppSettings()
            yield AppInfo("")
            yield Splash(self.SPLASH_IMAGE)
            yield AppHelp(commander_help())
            yield MarkdownViewer()
        yield Input(placeholder=f"Message {self.engine.nickname()}", suggester=suggester)
        yield footer

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.enable_controls(False)
        self.screen.title = self.APP_TITLE
        self.screen.sub_title = self.engine.ai_model_name()
        self.md_console.set_class(True, "-hidden")
        self.md_console.show_table_of_contents = False
        self._setup()
        self.md_console.set_interval(0.25, self._cb_refresh_console)

    def on_markdown_viewer_navigator_updated(self) -> None:
        """Refresh bindings for forward / back when the document changes."""
        self.refresh_bindings()

    async def action_back(self) -> None:
        """Navigate backwards."""
        await self.md_console.back()

    async def action_forward(self) -> None:
        """Navigate forwards."""
        await self.md_console.forward()

    def action_toggle_table_of_contents(self) -> None:
        """Toggles display of the table of contents."""
        self.md_console.show_table_of_contents = not self.md_console.show_table_of_contents

    def check_action(self, action: str, _) -> Optional[bool]:
        """Check if certain actions can be performed."""
        if action == "forward" and self.md_console.navigator.end:
            # Disable footer link if we can't go forward
            return None
        if action == "back" and self.md_console.navigator.start:
            # Disable footer link if we can't go backward
            return None
        # All other keys display as normal
        return True

    def enable_controls(self, enable: bool = True) -> None:
        """Enable all UI controls (header, input and footer)."""
        self.header.disabled = not enable
        self.line_input.loading = not enable
        self.footer.disabled = not enable

    def activate_markdown(self) -> None:
        """Activate the Markdown console."""
        self.md_console.go(self._console_path)
        self.md_console.set_class(False, "-hidden")
        self.md_console.scroll_end(animate=False)

    def action_clear(self, overwrite: bool = True) -> None:
        """Clear the output console."""
        is_new: bool = not file_is_not_empty(str(self._console_path)) or overwrite
        with open(self._console_path, "w" if overwrite else "a", encoding=Charset.UTF_8.val) as f_console:
            f_console.write(
                f"{'---' + os.linesep * 2 if not is_new else ''}"
                f"{'# ' + now(DATE_FORMAT) + os.linesep * 2 if is_new else ''}"
                f"## {AppIcons.STARTED} {now(TIME_FORMAT)}\n\n"
            )
            f_console.flush()
            self._re_render = True
        self.reply(f"{msg.welcome(prompt.user.title())}")

    async def action_speaking(self) -> None:
        """Toggle Speaking ON/OFF."""
        self._ask_and_reply("/speak")

    async def action_debugging(self) -> None:
        """Toggle Debugging ON/OFF."""
        self._ask_and_reply("/debug")

    @work(thread=True, exclusive=True)
    async def action_ptt(self) -> None:
        """Push-To-Talk STT as input method."""
        self.enable_controls(False)
        if spoken_text := self.engine.speech_to_text():
            self.display_text(f"{self.username}: {spoken_text}")
            if self._ask_and_reply(spoken_text):
                await self.suggester.add_suggestion(spoken_text)
                suggestions = await self.suggester.suggestions()
                cache.save_query_history(suggestions)
        self.enable_controls()

    @on(Input.Submitted)
    async def on_submit(self, submitted: Input.Submitted) -> None:
        """A coroutine to handle a input submission."""
        question: str = submitted.value
        self.line_input.clear()
        self.display_text(f"{self.username}: {question}")
        if self._ask_and_reply(question):
            await self.suggester.add_suggestion(question)
            suggestions = await self.suggester.suggestions()
            cache.save_query_history(suggestions)

    async def _write_markdown(self) -> None:
        """Write buffered text to the markdown file."""
        if len(self._display_buffer) > 0:
            with open(self._console_path, "a", encoding=Charset.UTF_8.val) as f_console:
                prev_text: str | None = None
                while len(self._display_buffer) > 0:
                    if (text := self._display_buffer.pop(0)) == prev_text:
                        continue
                    prev_text = text
                    final_text: str = text_formatter.beautify(f"{ensure_endswith(text, os.linesep * 2)}")
                    f_console.write(final_text)
                    f_console.flush()
                self._re_render = True

    def display_text(self, markdown_text: str) -> None:
        """Send the text to the Markdown console."""
        self._display_buffer.append(markdown_text)

    def reply(self, message: str) -> None:
        """Reply to the user with the AI response.
        :param message: The message to reply to the user.
        """
        prev_msg: str = self._display_buffer[-1] if self._display_buffer else ''
        if message and prev_msg != message:
            log.debug(message)
            self.display_text(f"{self.nickname}: {message}")
            if configs.is_speak:
                self.engine.text_to_speech(message, f"{self.nickname}: ")

    def reply_error(self, message: str) -> None:
        """Reply API or system errors.
        :param message: The error message to be displayed.
        """
        prev_msg: str = self._display_buffer[-1] if self._display_buffer else ''
        if message and prev_msg != message:
            log.error(message)
            self.display_text(f"{self.nickname}: Error: {message}")
            if configs.is_speak:
                self.engine.text_to_speech(f"Error: {message}", f"{self.nickname}: ")

    async def _cb_refresh_console(self) -> None:
        """Callback to handle markdown console updates."""
        if not self._console_path.exists():
            self.action_clear()
        await self._write_markdown()
        if self._re_render:
            self._re_render = False
            await self.md_console.go(self._console_path)
            self.md_console.scroll_end(animate=False)

    def _cb_reply_event(self, ev: Event, error: bool = False) -> None:
        """Callback to handle reply events.
        :param ev: The reply event.
        :param error: Whether the event is an error not not.
        """
        if message := ev.args.message:
            if error:
                self.reply_error(message)
            else:
                if ev.args.verbosity.casefold() == "normal" or configs.is_debug:
                    self.reply(message)

    def _cb_mic_listening_event(self, ev: Event) -> None:
        """Callback to handle microphone listening events.
        :param ev: The microphone listening event.
        """
        self.header.notifications.listening = ev.args.listening
        if ev.args.listening:
            self.reply(msg.listening())

    def _cb_device_changed_event(self, ev: Event) -> None:
        """Callback to handle audio input device changed events.
        :param ev: The device changed event.
        """
        self.reply(msg.device_switch(str(ev.args.device)))

    def _cb_mode_changed_event(self, ev: Event) -> None:
        """Callback to handle mode changed events.
        :param ev: The mode changed event.
        """
        self._mode: RouterMode = RouterMode.of_name(ev.args.mode)
        if not self._mode.is_default:
            self.reply(
                f"{msg.enter_qna()} \n"
                f"```\nContext:  {ev.args.sum_path},   {ev.args.glob} \n```\n"
                f"`{msg.press_esc_enter()}` \n\n"
                f"> {msg.qna_welcome()}")

    @work(thread=True, exclusive=True)
    def _ask_and_reply(self, question: str) -> bool:
        """Ask the question to the AI, and provide the reply.
        :param question: The question to ask to the AI engine.
        """
        status = True
        processor: AIProcessor = self.mode.processor
        self.enable_controls(False)
        assert isinstance(processor, AIProcessor)

        try:
            if command := re.search(self.RE_ASKAI_CMD, question):
                with StringIO() as buf, redirect_stdout(buf):
                    args: list[str] = list(
                        filter(lambda a: a and a != "None", re.split(r"\s", f"{command.group(1)} {command.group(2)}"))
                    )
                    ask_cli(args, standalone_mode=False)
                    if output := buf.getvalue():
                        self.display_text(f"\n```bash\n{strip_escapes(output)}\n```")
            elif not (reply := cache.read_reply(question)):
                log.debug('Response not found for "%s" in cache. Querying from %s.', question, self.engine.nickname())
                self.reply(msg.wait())
                if output := processor.process(question):
                    self.reply(output)
            else:
                log.debug("Reply found for '%s' in cache.", question)
                self.reply(reply)
        except (NotImplementedError, ImpossibleQuery) as err:
            self.reply_error(str(err))
        except (MaxInteractionsReached, InaccurateResponse) as err:
            self.reply_error(msg.unprocessable(str(err)))
        except UsageError as err:
            self.reply_error(msg.invalid_command(err))
        except IntelligibleAudioError as err:
            self.reply_error(msg.intelligible(err))
        except RateLimitError:
            self.reply_error(msg.quote_exceeded())
            status = False
        except TerminatingQuery:
            status = False

        self.enable_controls()

        return status

    def _startup(self) -> None:
        """Initialize the application."""
        os.chdir(Path.home())
        askai_bus = AskAiEvents.bus(ASKAI_BUS_NAME)
        askai_bus.subscribe(REPLY_EVENT, self._cb_reply_event)
        askai_bus.subscribe(REPLY_ERROR_EVENT, partial(self._cb_reply_event, error=True))
        nltk.download("averaged_perceptron_tagger", quiet=True, download_dir=CACHE_DIR)
        recorder.setup()
        scheduler.start()
        askai_bus.subscribe(MIC_LISTENING_EVENT, self._cb_mic_listening_event)
        askai_bus.subscribe(DEVICE_CHANGED_EVENT, self._cb_device_changed_event)
        askai_bus.subscribe(MODE_CHANGED_EVENT, self._cb_mode_changed_event)
        log.info("AskAI is ready to use!")

    @work(thread=True, exclusive=True)
    def _setup(self) -> None:
        """Setup the TUI controls."""
        player.start_delay()
        self.splash.set_class(True, "-hidden")
        self.activate_markdown()
        self.action_clear(overwrite=False)
        self.enable_controls()
        self.reply(f"{msg.welcome(prompt.user.title())}")
        self.line_input.focus(False)
