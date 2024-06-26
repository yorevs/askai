#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core
      @file: askai.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import logging as log
import os
import re
import sys
from functools import partial
from pathlib import Path
from threading import Thread
from typing import List, Optional, TypeAlias

import nltk
import pause
from click import UsageError
from clitt.core.term.cursor import cursor
from clitt.core.term.screen import screen
from clitt.core.term.terminal import terminal
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import is_debugging, sysout
from hspylib.core.tools.text_tools import elide_text
from hspylib.modules.application.exit_status import ExitStatus
from hspylib.modules.application.version import Version
from hspylib.modules.eventbus.event import Event
from openai import RateLimitError

from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.askai_events import (ASKAI_BUS_NAME, AskAiEvents, DEVICE_CHANGED_EVENT, MIC_LISTENING_EVENT,
                                     REPLY_ERROR_EVENT, REPLY_EVENT)
from askai.core.askai_messages import msg
from askai.core.commander.commander import ask_cli, commands
from askai.core.component.audio_player import player
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.core.component.geo_location import geo_location
from askai.core.component.recorder import recorder
from askai.core.component.scheduler import scheduler
from askai.core.engine.ai_engine import AIEngine
from askai.core.enums.router_mode import RouterMode
from askai.core.features.router.ai_processor import AIProcessor
from askai.core.support.chat_context import ChatContext
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text, read_stdin
from askai.exception.exceptions import *

QueryString: TypeAlias = str | List[str] | None


class AskAi:
    """Responsible for the OpenAI functionalities."""

    SPLASH: str = classpath.get_resource("splash.txt").read_text(encoding=Charset.UTF_8.val)

    RE_ASKAI_CMD: str = r"^(?<!\\)/(\w+)( (.*))*$"

    @staticmethod
    def _abort():
        """Abort the execution and exit."""
        sys.exit(ExitStatus.FAILED.val)

    def __init__(
        self,
        interactive: bool,
        quiet: bool,
        debug: bool,
        tempo: int,
        query_prompt: str,
        engine_name: str,
        model_name: str,
        query_string: QueryString,
    ):
        self._interactive: bool = interactive
        self._ready: bool = False
        self._processing: Optional[bool] = None
        self._query_string: QueryString = query_string if isinstance(query_string, str) else ' '.join(query_string)
        self._query_prompt: str | None = query_prompt
        self._engine: AIEngine = shared.create_engine(engine_name, model_name)
        self._context: ChatContext = shared.create_context(self._engine.ai_token_limit())
        self._mode: RouterMode = RouterMode.TASK_SPLIT if interactive else RouterMode.NON_INTERACTIVE

        # Save setting configs from program arguments to remember later.
        configs.is_speak = not quiet
        configs.is_debug = is_debugging() or debug
        configs.tempo = tempo
        configs.is_interactive = interactive
        configs.engine = engine_name
        configs.model = model_name
        self._startup()

    def __str__(self) -> str:
        device_info = f"{recorder.input_device[1]}" if recorder.input_device else ""
        device_info += f", AUTO-SWAP {'ON' if recorder.is_auto_swap else '%RED%OFF'}"
        dtm = f" {geo_location.datetime} "
        speak_info = str(configs.tempo) + " @" + shared.engine.configs.tts_voice
        cur_dir = elide_text(str(Path(os.curdir).absolute()), 67, "…")
        return (
            f"%GREEN%"
            f"AskAI v{Version.load(load_dir=classpath.source_path())} %EOL%"
            f"{dtm.center(80, '=')} %EOL%"
            f"     Engine: {self.engine} %EOL%"
            f"   Language: {configs.language} %EOL%"
            f"    WorkDir: {cur_dir} %EOL%"
            f"{'-' * 80} %EOL%"
            f" Microphone: {device_info or '%RED%Undetected'} %GREEN%%EOL%"
            f"  Debugging: {'ON' if self.is_debugging else '%RED%OFF'} %GREEN%%EOL%"
            f"   Speaking: {'ON, tempo: ' + speak_info if self.is_speak else '%RED%OFF'} %GREEN%%EOL%"
            f"    Caching: {'ON, TTL: ' + str(configs.ttl) if cache.is_cache_enabled() else '%RED%OFF'} %GREEN%%EOL%"
            f"{'=' * 80}%EOL%%NC%"
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
    def cache_enabled(self) -> bool:
        return configs.is_cache

    @property
    def is_interactive(self) -> bool:
        return self._interactive

    @property
    def is_debugging(self) -> bool:
        return configs.is_debug

    @property
    def is_speak(self) -> bool:
        return configs.is_speak

    @property
    def loading(self) -> bool:
        return self._processing

    @loading.setter
    def loading(self, processing: bool) -> None:
        if processing:
            self.reply(msg.wait())
        elif not processing and self._processing is not None and processing != self._processing:
            terminal.cursor.erase_line()
        self._processing = processing

    def run(self) -> None:
        """Run the application."""
        while query := (self._query_string or self._input()):
            status, output = self._ask_and_reply(query)
            if not (status and output):
                query = None
                break
            else:
                cache.save_reply(query, output)
                cache.save_query_history()
                if not self.is_interactive:
                    break
        if query == '':
            self.reply(msg.goodbye())
        sysout("%NC%")

    def reply(self, message: str) -> None:
        """Reply to the user with the AI response.
        :param message: The message to reply to the user.
        """
        if message:
            if self.is_speak:
                self.engine.text_to_speech(message, f"{shared.nickname}: ")
            else:
                display_text(message, f"{shared.nickname}: ")

    def reply_error(self, message: str) -> None:
        """Reply API or system errors.
        :param message: The error message to be displayed.
        """
        if message:
            log.error(message)
            if self.is_speak:
                self.engine.text_to_speech(f"Error: {message}", f"{shared.nickname}: ")
            else:
                display_text(f"%RED%Error: {message}%NC%", f"{shared.nickname}: ")

    def _input(self) -> Optional[str]:
        """Read the user input from stdin."""
        return shared.input_text(f"{shared.username}: ", f"Message {self.engine.nickname()}")

    def _cb_reply_event(self, ev: Event, error: bool = False) -> None:
        """Callback to handle reply events.
        :param ev: The reply event.
        :param error: Whether the event is an error not not.
        """
        if message := ev.args.message:
            if error:
                self.reply_error(message)
            else:
                if ev.args.verbosity.casefold() == "normal" or self.is_debugging:
                    if ev.args.erase_last:
                        cursor.erase_line()
                    self.reply(message)

    def _cb_mic_listening_event(self, ev: Event) -> None:
        """Callback to handle microphone listening events.
        :param ev: The microphone listening event.
        """
        if ev.args.listening:
            self.reply(msg.listening())

    def _cb_device_changed_event(self, ev: Event) -> None:
        """Callback to handle audio input device changed events.
        :param ev: The device changed event.
        """
        cursor.erase_line()
        self.reply(msg.device_switch(str(ev.args.device)))

    def _splash(self) -> None:
        """Display the AskAI splash screen."""
        splash_interval = 250
        screen.clear()
        sysout(f"%GREEN%{self.SPLASH}%NC%")
        while not self._ready:
            pause.milliseconds(splash_interval)
        screen.clear()

    def _startup(self) -> None:
        """Initialize the application."""
        askai_bus = AskAiEvents.bus(ASKAI_BUS_NAME)
        askai_bus.subscribe(REPLY_EVENT, self._cb_reply_event)
        askai_bus.subscribe(REPLY_ERROR_EVENT, partial(self._cb_reply_event, error=True))
        if self.is_interactive:
            splash_thread: Thread = Thread(daemon=True, target=self._splash)
            splash_thread.start()
            nltk.download("averaged_perceptron_tagger", quiet=True, download_dir=CACHE_DIR)
            cache.set_cache_enable(self.cache_enabled)
            KeyboardInput.preload_history(cache.load_history(commands()))
            recorder.setup()
            scheduler.start()
            player.start_delay()
            self._ready = True
            splash_thread.join()
            display_text(self, markdown=False)
            self.reply(msg.welcome(os.getenv("USER", "you")))
        elif self.is_speak:
            recorder.setup()
            player.start_delay()
        askai_bus.subscribe(MIC_LISTENING_EVENT, self._cb_mic_listening_event)
        askai_bus.subscribe(DEVICE_CHANGED_EVENT, self._cb_device_changed_event)
        log.info("AskAI is ready to use!")

    def _ask_and_reply(self, question: str) -> tuple[bool, Optional[str]]:
        """Ask the question to the AI, and provide the reply.
        :param question: The question to ask to the AI engine.
        """
        status, output = True, None
        processor: AIProcessor = self.mode
        try:
            if command := re.search(self.RE_ASKAI_CMD, question):
                args: list[str] = list(
                    filter(lambda a: a and a != "None", re.split(r"\s", f"{command.group(1)} {command.group(2)}"))
                )
                ask_cli(args, standalone_mode=False)
            elif not (reply := cache.read_reply(question)):
                log.debug('Response not found for "%s" in cache. Querying from %s.', question, self.engine.nickname())
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.wait())
                output = processor.process(question, context=read_stdin(), query_prompt=self._query_prompt)
                if output or msg.no_output("processor"):
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
        except IntelligibleAudioError as err:
            self.reply_error(msg.intelligible(err))
        except RateLimitError:
            self.reply_error(msg.quote_exceeded())
            status = False
        except TerminatingQuery:
            status = False

        return status, output
