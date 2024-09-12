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
from askai.core.askai import AskAi
from askai.core.askai_configs import configs
from askai.core.askai_events import *
from askai.core.askai_messages import msg
from askai.core.commander.commander import commands
from askai.core.component.audio_player import player
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.core.component.recorder import recorder
from askai.core.component.scheduler import scheduler
from askai.core.enums.router_mode import RouterMode
from askai.core.model.ai_reply import AIReply
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text
from clitt.core.term.cursor import cursor
from clitt.core.term.screen import screen
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from hspylib.modules.eventbus.event import Event
from pathlib import Path
from rich.progress import Progress
from threading import Thread
from typing import List, Optional, TypeAlias

import logging as log
import nltk
import os
import pause

QueryString: TypeAlias = str | List[str] | None


class AskAiCli(AskAi):
    """The AskAI CLI application."""

    def __init__(
        self,
        interactive: bool,
        speak: bool,
        debug: bool,
        cacheable: bool,
        tempo: int,
        query_prompt: str,
        engine_name: str,
        model_name: str,
        query_string: QueryString,
    ):

        configs.is_interactive = interactive if not query_prompt else False
        super().__init__(interactive, speak, debug, cacheable, tempo, engine_name, model_name)
        os.environ["ASKAI_APP"] = (self.RunModes.ASKAI_CLI if interactive else self.RunModes.ASKAI_CMD).value
        self._ready: bool = False
        self._progress = Progress()
        self._query_prompt = query_prompt
        self._query_string: QueryString = query_string if isinstance(query_string, str) else " ".join(query_string)
        self._startup()

    def run(self) -> None:
        """Run the application."""
        while question := (self._query_string or self._input()):
            status, output = self.ask_and_reply(question)
            if not status:
                question = None
                break
            elif output:
                cache.save_reply(question, output)
                cache.save_input_history()
                with open(self._console_path, "a+") as f_console:
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
            elif not configs.is_interactive:
                display_text(text_formatter.strip_format(text), f"{shared.nickname}", markdown=False)
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
        return shared.input_text(f"{shared.username}", f"Message {self.engine.nickname()}")

    def _cb_reply_event(self, ev: Event) -> None:
        """Callback to handle reply events.
        :param ev: The event object representing the reply event.
        """
        reply: AIReply
        if reply := ev.args.reply:
            if reply.is_error:
                self._reply_error(reply)
            else:
                if ev.args.reply.verbosity.match(configs.verbosity) or configs.is_debug:
                    if ev.args.erase_last:
                        cursor.erase_line()
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
        display_text(f"%GREEN%{self.SPLASH}%NC%", markdown=False)
        while not self._ready:
            pause.milliseconds(interval)
        screen.clear()

    def _startup(self) -> None:
        """Initialize the application components."""
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
            task = self._progress.add_task("[green]Starting up...", total=len(tasks))
            with self._progress:
                os.chdir(Path.home())
                self._progress.update(task, advance=1, description="[green]Downloading nltk data")
                nltk.download("averaged_perceptron_tagger", quiet=True, download_dir=CACHE_DIR)
                cache.cache_enable = configs.is_cache
                self._progress.update(task, advance=1, description="[green]Loading input history")
                KeyboardInput.preload_history(cache.load_input_history(commands()))
                self._progress.update(task, advance=1, description="[green]Starting scheduler")
                scheduler.start()
                self._progress.update(task, advance=1, description="[green]Setting up recorder")
                recorder.setup()
                self._progress.update(task, advance=1, description="[green]Starting player delay")
                player.start_delay()
                self._progress.update(task, advance=1, description="[green]Finalizing startup")
                pause.seconds(1)
            self._ready = True
            splash_thread.join()
            askai_bus.subscribe(MIC_LISTENING_EVENT, self._cb_mic_listening_event)
            askai_bus.subscribe(DEVICE_CHANGED_EVENT, self._cb_device_changed_event)
            askai_bus.subscribe(MODE_CHANGED_EVENT, self._cb_mode_changed_event)
            display_text(str(self), markdown=False)
            self._reply(AIReply.info(msg.welcome(os.getenv("USER", "you"))))
        elif configs.is_speak:
            recorder.setup()
            player.start_delay()
        log.info("AskAI is ready to use!")
