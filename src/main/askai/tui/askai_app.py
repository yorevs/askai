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
from functools import partial
from io import StringIO
from pathlib import Path
from typing import Callable, Optional

import nltk
from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.askai_events import ASKAI_BUS_NAME, AskAiEvents, REPLY_ERROR_EVENT, REPLY_EVENT
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.askai_settings import settings
from askai.core.commander.commander import ask_cli
from askai.core.component.audio_player import player
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.core.component.recorder import recorder
from askai.core.component.scheduler import scheduler
from askai.core.engine.ai_engine import AIEngine
from askai.core.features.router import router
from askai.core.support.chat_context import ChatContext
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.exception.exceptions import ImpossibleQuery, InaccurateResponse, MaxInteractionsReached, TerminatingQuery
from askai.tui.app_header import Header
from askai.tui.app_suggester import InputSuggester
from askai.tui.app_widgets import AppInfo, Splash, AppSettings
from click import UsageError
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import is_debugging
from hspylib.core.tools.text_tools import elide_text, ensure_endswith, strip_escapes
from hspylib.core.zoned_datetime import now
from hspylib.modules.application.version import Version
from hspylib.modules.eventbus.event import Event
from openai import RateLimitError
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Footer, Input, MarkdownViewer

SOURCE_DIR: Path = classpath.source_path()

RESOURCE_DIR: Path = classpath.resource_path()


class AskAiApp(App):
    """The AskAI Textual application."""

    CSS_PATH = f"{RESOURCE_DIR}/askai.tcss"

    # fmt: off
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear", "Clear Console"),
        ("t", "toggle_table_of_contents", "TOC"),
        ("d", "debugging", "Debugging"),
        ("s", "speaking", "Speaking"),
    ]
    # fmt: on

    ENABLE_COMMAND_PALETTE = False

    SPLASH_IMAGE: str = classpath.get_resource("splash.txt").read_text(encoding=Charset.UTF_8.val)

    RE_ASKAI_CMD: str = r"^(?<!\\)/(\w+)( (.*))*$"

    def __init__(self, quiet: bool, debug: bool, tempo: int, engine_name: str, model_name: str):
        super().__init__()
        self._session_id = now("%Y%m%d")[:8]
        self._question: str | None = None
        self._engine: AIEngine = shared.create_engine(engine_name, model_name)
        self._context: ChatContext = shared.create_context(self._engine.ai_token_limit())
        self._console_path = Path(f"{CACHE_DIR}/askai-{self.session_id}.md")
        self._re_render = True
        self._suggester = InputSuggester(self.load_history(), case_sensitive=False)
        if not self._console_path.exists():
            self._console_path.touch()
        # Setting configs from program args.
        configs.is_speak = not quiet
        configs.is_debug = is_debugging() or debug
        configs.tempo = tempo

    def __str__(self) -> str:
        device_info = f"{recorder.input_device[1]}" if recorder.input_device else ""
        device_info += f", AUTO-SWAP {'ON' if recorder.is_auto_swap else 'OFF'}"
        speak_info = str(configs.tempo) + " @" + shared.engine.configs.tts_voice
        cur_dir = elide_text(str(Path(os.curdir).absolute()), 67, "…")
        return (
            f"{'=' * 80} \n"
            f"     Engine: {self.engine} \n"
            f"   Language: {configs.language} \n"
            f"    WorkDir: {cur_dir} \n"
            f"{'-' * 80} \n"
            f" Microphone: {device_info or 'Undetected'} \n"
            f"  Debugging: {'ON' if self.is_debugging else 'OFF'} \n"
            f"   Speaking: {'ON, tempo: ' + speak_info if self.is_speak else 'OFF'} \n"
            f"    Caching: {'ON, TTL: ' + str(configs.ttl) if cache.is_cache_enabled() else 'OFF'} \n"
            f"{'=' * 80}"
        )

    @property
    def engine(self) -> AIEngine:
        return self._engine

    @property
    def context(self) -> ChatContext:
        return self._context

    @property
    def cache_enabled(self) -> bool:
        return configs.is_cache

    @property
    def question(self) -> str:
        return self._question

    @property
    def is_debugging(self) -> bool:
        return configs.is_debug

    @property
    def is_speak(self) -> bool:
        return configs.is_speak

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
        return self._suggester

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
        all_settings = [("Setting", "Value")]
        for s in settings.settings.search():
            r: tuple[str, ...] = str(s.name), str(s.value)
            all_settings.append(r)
        return all_settings

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        footer = Footer()
        footer.upper_case_keys = True
        yield Header()
        with ScrollableContainer():
            yield AppSettings()
            yield AppInfo("")
            yield Splash(self.SPLASH_IMAGE)
            yield MarkdownViewer()
        yield Input(placeholder=f"Message {self.engine.nickname()}", suggester=self._suggester)
        yield footer

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.screen.title = f"AskAI v{Version.load(load_dir=classpath.source_path())}"
        self.screen.sub_title = self.engine.ai_model_name()
        self.enable_controls(False)
        self.md_console.set_class(True, "-hidden")
        self.md_console.show_table_of_contents = False
        self.md_console.set_interval(0.7, self._cb_refresh_console)
        self._startup()

    def on_markdown_viewer_navigator_updated(self) -> None:
        """Refresh bindings for forward / back when the document changes."""
        self.refresh_bindings()

    def action_toggle_table_of_contents(self) -> None:
        """Toggles display of the table of contents."""
        self.md_console.show_table_of_contents = not self.md_console.show_table_of_contents

    def enable_controls(self, enable: bool = True):
        """Enable all UI controls (header, input and footer)."""
        self.header.disabled = not enable
        self.line_input.loading = not enable
        self.footer.disabled = not enable
        if enable:
            self.line_input.focus()

    def load_history(self) -> list[str]:
        """TODO"""
        # fmt: off
        history = [
            "/debug", "/devices", "/help",
            "/settings", "/speak", "/tempo",
            "/voices", "/forget"
        ]
        history.extend(cache.read_query_history())
        # fmt: on
        return history

    @work
    async def activate_markdown(self) -> None:
        """Activate the Markdown console."""
        await self.md_console.go(self._console_path)
        self.md_console.set_class(False, "-hidden")

    @work(thread=True)
    async def action_clear(self) -> None:
        """Clear the output console."""
        self.enable_controls(False)
        with open(self._console_path, "w", encoding=Charset.UTF_8.val) as f_console:
            f_console.write(f"---\n\n# {now()}\n\n")
            f_console.flush()
            self._re_render = True
        self.reply(f"{msg.welcome(prompt.user.title())}")
        self.enable_controls(True)

    async def action_speaking(self) -> None:
        """Toggle Speaking ON/OFF."""
        self._ask_and_reply("/speak", self._update_app_info)

    async def action_debugging(self) -> None:
        """Toggle Debugging ON/OFF."""
        self._ask_and_reply("/debug", self._update_app_info)

    @work(thread=True)
    def display_text(self, markdown_text: str) -> None:
        """Send the text to the Markdown console."""
        with open(self._console_path, "a", encoding=Charset.UTF_8.val) as f_console:
            final_text: str = text_formatter.beautify(f"{ensure_endswith(markdown_text, os.linesep * 2)}")
            f_console.write(final_text)
            f_console.flush()
            self._re_render = True

    @on(Input.Submitted)
    async def on_submit(self, submitted: Input.Submitted) -> None:
        """A coroutine to handle a input submission."""
        question: str = submitted.value
        self.line_input.clear()
        self.line_input.loading = True
        self.display_text(f"{self.username}: {question}")
        if self._ask_and_reply(question):
            await self.suggester.add_suggestion(question)
            suggestions = await self.suggester.suggestions()
            cache.save_query_history(suggestions)

    def reply(self, message: str) -> None:
        """Reply to the user with the AI response.
        :param message: The message to reply to the user.
        """
        log.debug(message)
        self.display_text(f"{self.nickname}: {message}")
        if self.is_speak:
            self.engine.text_to_speech(message, f"{self.nickname}: ")

    def reply_error(self, message: str) -> None:
        """Reply API or system errors.
        :param message: The error message to be displayed.
        """
        log.error(message)
        self.display_text(f"{self.nickname}: Error: {message}")
        if self.is_speak:
            self.engine.text_to_speech(f"Error: {message}", f"{self.nickname}: ")

    def _update_app_info(self, _: int, __: str) -> None:
        """Update the application information text. This callback is required because ask_and_reply is async."""
        self.info.info_text = str(self)
        self.header.clock.debugging = self.is_debugging
        self.header.clock.speaking = self.is_speak
        self.settings.data = self.app_settings

    def _cb_reply_event(self, ev: Event, error: bool = False) -> None:
        """Callback to handle reply events.
        :param ev: The reply event.
        :param error: Whether the event is an error not not.
        """
        if error:
            self.reply_error(ev.args.message)
        else:
            verbose = ev.args.verbosity.lower()
            if verbose == "normal" or self.is_debugging:
                self.reply(ev.args.message)

    async def _cb_refresh_console(self) -> None:
        """Callback to handle markdown console updates."""
        if self._re_render:
            self._re_render = False
            await self.md_console.go(self._console_path)
            self.md_console.scroll_end(animate=False)

    @work(thread=True)
    async def _ask_and_reply(self, question: str, cb_on_finish: Callable[[bool, str], None] = None) -> bool:
        """Ask the question and provide the reply.
        :param question: The question to ask to the AI engine.
        """
        status = True
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
                self.reply(message=msg.wait())
                if output := router.process(question):
                    self.reply(output)
            else:
                log.debug("Reply found for '%s' in cache.", question)
                self.reply(reply)
        except (NotImplementedError, ImpossibleQuery) as err:
            self.reply_error(str(err))
        except (MaxInteractionsReached, InaccurateResponse, ValueError, AttributeError) as err:
            self.reply_error(msg.unprocessable(str(err)))
        except UsageError as err:
            self.reply_error(msg.invalid_command(err))
        except RateLimitError:
            self.reply_error(msg.quote_exceeded())
            status = False
        except TerminatingQuery:
            status = False

        if cb_on_finish:
            cb_on_finish(status, output)

        self.line_input.loading = False

        return status

    @work(thread=True)
    async def _startup(self) -> None:
        """Initialize the application."""
        askai_bus = AskAiEvents.get_bus(ASKAI_BUS_NAME)
        askai_bus.subscribe(REPLY_EVENT, self._cb_reply_event)
        askai_bus.subscribe(REPLY_ERROR_EVENT, partial(self._cb_reply_event, error=True))
        nltk.download("averaged_perceptron_tagger", quiet=True, download_dir=CACHE_DIR)
        cache.set_cache_enable(self.cache_enabled)
        player.start_delay()
        scheduler.start()
        recorder.setup()
        self.info.info_text = str(self)
        with open(self._console_path, "a", encoding=Charset.UTF_8.val) as f_console:
            f_console.write(f"---\n\n# {now()}\n\n")
            f_console.flush()
        # At this point the application is ready.
        self.splash.set_class(True, "-hidden")
        self.activate_markdown()
        self.reply(f"{msg.welcome(prompt.user.title())}")
        self.enable_controls()
        log.info("AskAI is ready to use!")
