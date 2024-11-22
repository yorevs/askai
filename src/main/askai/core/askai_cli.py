#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core
      @file: askai_cli.py
   @created: Fri, 9 Aug 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import logging as log
import os
import signal
from pathlib import Path
from textwrap import indent
from threading import Thread
from typing import Optional

import nltk
import pause
from clitt.core.term.cursor import cursor
from clitt.core.term.screen import screen
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import console_out
from hspylib.core.zoned_datetime import now, TIME_FORMAT
from hspylib.modules.eventbus.event import Event
from rich.progress import Progress

from askai.core.askai import AskAi
from askai.core.askai_configs import configs
from askai.core.askai_events import *
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.commander.commander import commands
from askai.core.component.audio_player import player
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.core.component.recorder import recorder
from askai.core.component.scheduler import scheduler
from askai.core.enums.router_mode import RouterMode
from askai.core.model.ai_reply import AIReply
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text
from askai.tui.app_icons import AppIcons


class AskAiCli(AskAi):
    """The AskAI CLI application."""

    def __init__(
        self,
        speak: bool,
        debug: bool,
        cacheable: bool,
        tempo: int,
        query_prompt: str,
        engine_name: str,
        model_name: str,
        query_string: str | None,
        mode: RouterMode,
    ):

        super().__init__(speak, debug, cacheable, tempo, engine_name, model_name, mode)
        self._ready: bool = False
        self._query_prompt: str = query_prompt
        self._query_string: str | None = query_string
        self._startup()

    def run(self) -> None:
        """Run the application."""
        signal.signal(signal.SIGINT, self.abort)
        while question := (self._query_string or self._input()):
            status, output = self.ask_and_reply(question)
            if not status:
                question = None
                break
            elif output:
                cache.save_reply(question, output)
                cache.save_input_history()
                # FIXME This is only writing the final answer to the markdown file.
                with open(self.console_path, "a+", encoding=Charset.UTF_8.val) as f_console:
                    f_console.write(f"{shared.username_md}{question}\n\n")
                    f_console.write(f"{shared.nickname_md}{output}\n\n")
                    f_console.flush()
            if not configs.is_interactive:
                break
        if question == "":
            self._reply(AIReply.info(msg.goodbye()))
        display_text("", markdown=False)

    def _reply(self, reply: AIReply) -> None:
        """Reply to the user with the AI-generated response.
        :param reply: The reply message to send as a reply to the user.
        """
        if reply and (text := msg.translate(reply.message)):
            log.debug(reply.message)
            if configs.is_speak and reply.is_speakable:
                self.engine.text_to_speech(text, f"{shared.nickname}")
            else:
                display_text(text, f"{shared.nickname}")

    def _reply_error(self, reply: AIReply) -> None:
        """Reply to the user with an AI-generated error message or system error.
        :param reply: The error reply message to be displayed to the user.
        """
        if reply and (text := msg.translate(reply.message)):
            log.error(reply.message)
            if configs.is_speak and reply.is_speakable:
                self.engine.text_to_speech(f"Error: {text}", f"{shared.nickname}")
            else:
                display_text(f"%RED%Error: {text}%NC%", f"{shared.nickname}")

    def _input(self) -> Optional[str]:
        """Read the user input from stdin.
        :return: The user's input as a string, or None if no input is provided.
        """
        return shared.input_text(f"{shared.username}", f"{msg.t('Message')} {self.engine.nickname()}")

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
                    if ev.args.erase_last:
                        cursor.erase_line()
                    self._reply(reply)

    def _cb_mode_changed_event(self, ev: Event) -> None:
        """Callback to handle mode change events.
        :param ev: The event object representing the mode change.
        """
        self.mode: RouterMode = RouterMode.of_name(ev.args.mode)
        if self.mode == RouterMode.QNA:
            welcome_msg = self.mode.welcome(sum_path=ev.args.sum_path, sum_glob=ev.args.glob)
        else:
            welcome_msg = self.mode.welcome()

        events.reply.emit(reply=AIReply.info(welcome_msg or msg.welcome(prompt.user.title())))

    def _cb_mic_listening_event(self, ev: Event) -> None:
        """Callback to handle microphone listening events.
        :param ev: The event object representing the microphone listening event.
        """
        if ev.args.listening:
            self._reply(AIReply.info(msg.listening()))

    def _cb_device_changed_event(self, ev: Event) -> None:
        """Callback to handle audio input device change events.
        :param ev: The event object representing the device change.
        """
        cursor.erase_line()
        self._reply(AIReply.info(msg.device_switch(str(ev.args.device))))

    def _splash(self, interval: int = 250) -> None:
        """Display the AskAI splash screen until the system is fully started and ready. This method shows the splash
        screen during the startup process and hides it once the system is ready.
        :param interval: The interval in milliseconds for polling the startup status (default is 250 ms).
        """
        screen.clear()
        console_out.print(indent(self.SPLASH, " " * 13))
        while not self._ready:
            pause.milliseconds(interval)
        screen.clear()

    def _startup(self) -> None:
        """Initialize the application components."""
        progress: Progress = Progress()
        # List of tasks for progress tracking
        tasks = [
            "Downloading nltk data",
            "Loading input history",
            "Starting scheduler",
            "Setting up recorder",
            "Starting player delay",
            "Finalizing startup",
        ]
        # Start and manage the progress bar
        askai_bus = AskAiEvents.bus(ASKAI_BUS_NAME)
        askai_bus.subscribe(REPLY_EVENT, self._cb_reply_event)
        if configs.is_interactive:
            splash_thread: Thread = Thread(daemon=True, target=self._splash)
            splash_thread.start()
            task = progress.add_task(f'[green] {msg.t("Starting up...")}', total=len(tasks))
            with progress:
                os.chdir(Path.home())
                progress.update(task, advance=1, description=f'[green] {msg.t("Downloading nltk data")}')
                nltk.download("averaged_perceptron_tagger", quiet=True, download_dir=CACHE_DIR)
                cache.cache_enable = configs.is_cache
                progress.update(task, advance=1, description=f'[green] {msg.t("Loading input history")}')
                KeyboardInput.preload_history(cache.load_input_history(commands()))
                progress.update(task, advance=1, description=f'[green] {msg.t("Starting scheduler")}')
                scheduler.start()
                progress.update(task, advance=1, description=f'[green] {msg.t("Setting up recorder")}')
                recorder.setup()
                progress.update(task, advance=1, description=f'[green] {msg.t("Starting player delay")}')
                player.start_delay()
                progress.update(task, advance=1, description=f'[green] {msg.t("Finalizing startup")}')
                pause.seconds(1)
            self._ready = True
            splash_thread.join()
            askai_bus.subscribe(MIC_LISTENING_EVENT, self._cb_mic_listening_event)
            askai_bus.subscribe(DEVICE_CHANGED_EVENT, self._cb_device_changed_event)
            askai_bus.subscribe(MODE_CHANGED_EVENT, self._cb_mode_changed_event)
            display_text(str(self), markdown=False)
            self._reply(AIReply.info(self.mode.welcome()))
        elif configs.is_speak:
            nltk.download("averaged_perceptron_tagger", quiet=True, download_dir=CACHE_DIR)
            recorder.setup()
            player.start_delay()
        # Register the startup
        with open(self.console_path, "a+", encoding=Charset.UTF_8.val) as f_console:
            f_console.write(f"\n\n## {AppIcons.STARTED} {now(TIME_FORMAT)}\n\n")
            f_console.flush()
        log.info("AskAI is ready to use!")
