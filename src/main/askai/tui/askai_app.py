#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.tui.askai_app
      @file: askai_app.py
   @created: Mon, 29 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from pathlib import Path
from typing import Optional
import logging as log
import os

from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.core.tools.text_tools import ensure_endswith
from hspylib.core.zoned_datetime import DATE_FORMAT, now, TIME_FORMAT
from hspylib.modules.application.version import Version
from hspylib.modules.cli.vt100.vt_color import VtColor
from hspylib.modules.eventbus.event import Event
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Footer, Input, MarkdownViewer
import nltk

from askai.__classpath__ import classpath
from askai.core.askai import AskAi
from askai.core.askai_configs import configs
from askai.core.askai_events import *
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.commander.commander import commander_help
from askai.core.component.audio_player import player
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.core.component.recorder import recorder
from askai.core.component.scheduler import scheduler
from askai.core.engine.ai_engine import AIEngine
from askai.core.enums.router_mode import RouterMode
from askai.core.model.ai_reply import AIReply
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.tui.app_header import Header
from askai.tui.app_icons import AppIcons
from askai.tui.app_suggester import InputSuggester
from askai.tui.app_widgets import AppHelp, AppInfo, AppSettings, Splash, InputArea, InputActions

SOURCE_DIR: Path = classpath.source_path

RESOURCE_DIR: Path = classpath.resource_path


class AskAiApp(App[None]):
    """The AskAI Textual application."""

    APP_TITLE: str = f"AskAI v{Version.load(load_dir=classpath.source_path)}"

    CSS_PATH = f"{RESOURCE_DIR}/askai.tcss"

    # fmt: off
    BINDINGS = [
        ("q", "quit", " Quit"),
        ("c", "clear", " Clear"),
        ("d", "debugging", " Debugging"),
        ("s", "speaking", " Speaking"),
        ("a", "assistive", " Assistive"),
        ("ctrl+l", "ptt", " Push-to-Talk"),
        ("ctrl+s", "stop", " Stop-GenAi"),
    ]
    # fmt: on

    ENABLE_COMMAND_PALETTE = False

    def __init__(
        self, speak: bool, debug: bool, cacheable: bool, tempo: int, engine_name: str, model_name: str, mode: RouterMode
    ):
        super().__init__()
        self._askai: AskAi = AskAi(speak, debug, cacheable, tempo, engine_name, model_name, mode)
        self._re_render: bool = True
        self._display_buffer: list[str] = list()
        self._startup()

    def __str__(self) -> str:
        return VtColor.strip_colors(shared.app_info)

    @property
    def askai(self) -> AskAi:
        return self._askai

    @property
    def engine(self) -> AIEngine:
        return self.askai.engine

    @property
    def app_settings(self) -> list[tuple[str, ...]]:
        return self.askai.app_settings

    @property
    def console_path(self) -> Path:
        return self.askai.console_path

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
    def input_actions(self):
        return self.query_one(InputActions)

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

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        footer = Footer()
        footer.upper_case_keys = True
        footer.ctrl_to_caret = True
        yield Header()
        with ScrollableContainer():
            yield AppSettings()
            yield AppInfo()
            yield Splash(self.askai.SPLASH)
            yield AppHelp(commander_help())
            yield MarkdownViewer()
        yield InputArea(self.engine.nickname())
        yield footer

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.screen.title = self.APP_TITLE
        self.screen.sub_title = self.engine.ai_model_name()
        self.md_console.set_class(True, "-hidden")
        self.md_console.show_table_of_contents = False
        self.md_console.set_interval(0.25, self._cb_refresh_console)
        self.enable_controls(False)
        self._setup()

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
        """Check if a specific action can be performed.
        :param action: The name of the action to check.
        :param _: Unused parameter, typically a placeholder for additional context.
        :return: True if the action can be performed, None if it cannot.
        """
        if action == "forward" and self.md_console.navigator.end:
            # Disable footer link if we can't go forward
            return None
        if action == "back" and self.md_console.navigator.start:
            # Disable footer link if we can't go backward
            return None
        # All other keys display as normal
        return True

    @work(thread=True)
    def enable_controls(self, enable: bool = True) -> None:
        """Enable or disable all UI controls, including the header, input, and footer.
        :param enable: Whether to enable (True) or disable (False) the UI controls (default is True).
        """

        def _invoke_later_(arg: bool = True) -> None:
            self.input_actions.set_class(not arg, "-hidden")
            self.header.disabled = not arg
            self.line_input.loading = not arg
            self.footer.disabled = not arg

        self.call_from_thread(_invoke_later_, enable)

    def activate_markdown(self) -> None:
        """Activate the markdown console widget."""
        self.md_console.go(self.console_path)
        self.md_console.set_class(False, "-hidden")
        self.md_console.scroll_end(animate=False)

    def action_clear(self, overwrite: bool = True) -> None:
        """Clear the output console.
        :param overwrite: Whether to overwrite the existing content in the console (default is True).
        """
        is_new: bool = not file_is_not_empty(str(self.console_path)) or overwrite
        with open(self.console_path, "w" if overwrite else "a", encoding=Charset.UTF_8.val) as f_console:
            f_console.write(
                f"{'---' + os.linesep * 2 if not is_new else ''}"
                f"{'# ' + now(DATE_FORMAT) + os.linesep * 2 if is_new else ''}"
                f"## {AppIcons.STARTED} {now(TIME_FORMAT)}\n\n"
            )
            f_console.flush()
            self._re_render = True
        self._reply(AIReply.info(f"{msg.welcome(prompt.user.title())}"))

    async def action_speaking(self) -> None:
        """Toggle Speaking ON/OFF."""
        self.ask_and_reply("/speak")

    async def action_debugging(self) -> None:
        """Toggle Debugging ON/OFF."""
        self.ask_and_reply("/debug")

    async def action_assistive(self) -> None:
        """Toggle Assistive ON/OFF."""
        self.ask_and_reply("/assistive")

    @work(thread=True)
    async def action_ptt(self) -> None:
        """Handle the Push-To-Talk (PTT) action for Speech-To-Text (STT) input. This method allows the user to use
        Push-To-Talk as an input method, converting spoken words into text.
        """
        self.enable_controls(False)
        if spoken_text := self.engine.speech_to_text():
            self.display_text(f"{shared.username_md}: {spoken_text}")
            if self.ask_and_reply(spoken_text):
                await self.suggester.add_suggestion(spoken_text)
                suggestions = await self.suggester.suggestions()
                cache.save_input_history(suggestions)
        self.enable_controls()

    async def action_stop(self) -> None:
        """Stop generating response."""
        self.askai.abort()
        self.enable_controls()

    @on(Input.Submitted)
    async def on_submit(self, submitted: Input.Submitted) -> None:
        """A coroutine to handle input submission events.
        :param submitted: The event that contains the submitted data.
        """
        if question := submitted.value:
            self.line_input.clear()
            self.display_text(f"{shared.username_md}: {question}")
            if self.ask_and_reply(question):
                await self.suggester.add_suggestion(question)
                suggestions = await self.suggester.suggestions()
                cache.save_input_history(suggestions)

    async def _write_markdown(self) -> None:
        """Write buffered text to the markdown file.
        This method handles writing any accumulated or buffered text to a markdown file.
        """
        if len(self._display_buffer) > 0:
            with open(self.console_path, "a", encoding=Charset.UTF_8.val) as f_console:
                prev_text: str | None = None
                while len(self._display_buffer) > 0:
                    if (text := self._display_buffer.pop(0)) == prev_text:
                        continue
                    prev_text = text
                    final_text: str = text_formatter.beautify(f"{ensure_endswith(text, os.linesep * 2)}")
                    f_console.write(final_text)
                    f_console.flush()
                self._re_render = True

    async def _cb_refresh_console(self) -> None:
        """Callback to handle markdown console updates.
        This method is responsible for refreshing or updating the console display in markdown format.
        """
        if not self.console_path.exists():
            self.action_clear()
        await self._write_markdown()
        if self._re_render:
            self._re_render = False
            await self.md_console.go(self.console_path)
            self.md_console.scroll_end(animate=False)

    def _reply(self, reply: AIReply) -> None:
        """Reply to the user with the AI-generated response.
        :param reply: The reply message to send as a reply to the user.
        """
        prev_msg: str = self._display_buffer[-1] if self._display_buffer else ""
        if reply and prev_msg != reply.message:
            log.debug(reply.message)
            self.display_text(f"{shared.nickname_md} {reply.message}")
            if configs.is_speak and reply.is_speakable:
                self.engine.text_to_speech(reply.message, f"{shared.nickname_md} ")

    def _reply_error(self, reply: AIReply) -> None:
        """Reply to the user with an AI-generated error message or system error.
        :param reply: The error reply message to be displayed to the user.
        """
        prev_msg: str = self._display_buffer[-1] if self._display_buffer else ""
        if reply and prev_msg != reply.message:
            log.error(reply.message)
            self.display_text(f"{shared.nickname_md} Error: {reply.message}")
            if configs.is_speak and reply.is_speakable:
                self.engine.text_to_speech(f"Error: {reply.message}", f"{shared.nickname_md} ")

    def display_text(self, markdown_text: str) -> None:
        """Send the text to the Markdown console.
        :param markdown_text: the text to be displayed.
        """
        self._display_buffer.append(msg.translate(markdown_text))

    def _cb_reply_event(self, ev: Event) -> None:
        """Callback to handle reply events.
        :param ev: The event object representing the reply event.
        """
        reply: AIReply
        if reply := ev.args.reply:
            if reply.is_error:
                self._reply_error(reply)
            else:
                if ev.args.reply.match(configs.verbosity, configs.is_debug):
                    self._reply(reply)

    def _cb_mode_changed_event(self, ev: Event) -> None:
        """Callback to handle mode change events.
        :param ev: The event object representing the mode change.
        """
        self._mode: RouterMode = RouterMode.of_name(ev.args.mode)
        if not self._mode.is_default:
            sum_msg: str = (
                f"{msg.enter_qna()} \n"
                f"```\nContext:  {ev.args.sum_path},   {ev.args.glob} \n```\n"
                f"`{msg.press_esc_enter()}` \n\n"
                f"> {msg.qna_welcome()}"
            )
            events.reply.emit(reply=AIReply.info(sum_msg))

    def _cb_mic_listening_event(self, ev: Event) -> None:
        """Callback to handle microphone listening events.
        :param ev: The event object representing the microphone listening event.
        """
        self.header.notifications.listening = ev.args.listening
        if ev.args.listening:
            self._reply(AIReply.info(msg.listening()))

    def _cb_device_changed_event(self, ev: Event) -> None:
        """Callback to handle audio input device change events.
        :param ev: The event object representing the device change.
        """
        self._reply(AIReply.info(msg.device_switch(str(ev.args.device))))

    @work(thread=True, exclusive=True)
    def ask_and_reply(self, question: str) -> tuple[bool, Optional[str]]:
        """Ask the specified question to the AI and provide the reply.
        :param question: The question to ask the AI engine.
        :return: A tuple containing a boolean indicating success or failure, and the AI's reply as an optional string.
        """
        self.enable_controls(False)
        status, reply = self.askai.ask_and_reply(question)
        self.enable_controls()

        return status, reply

    def _startup(self) -> None:
        """Initialize the application components."""
        os.chdir(Path.home())
        askai_bus = AskAiEvents.bus(ASKAI_BUS_NAME)
        askai_bus.subscribe(REPLY_EVENT, self._cb_reply_event)
        nltk.download("averaged_perceptron_tagger", quiet=True, download_dir=CACHE_DIR)
        recorder.setup()
        scheduler.start()
        askai_bus.subscribe(MIC_LISTENING_EVENT, self._cb_mic_listening_event)
        askai_bus.subscribe(DEVICE_CHANGED_EVENT, self._cb_device_changed_event)
        askai_bus.subscribe(MODE_CHANGED_EVENT, self._cb_mode_changed_event)
        log.info("AskAI is ready to use!")

    @work(thread=True)
    def _setup(self) -> None:
        """Setup the TUI controls."""
        player.start_delay()
        self.splash.set_class(True, "-hidden")
        self.activate_markdown()
        self.action_clear(overwrite=False)
        self.enable_controls()
        self.line_input.focus(False)
