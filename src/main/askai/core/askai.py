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
from typing import List, Optional

import nltk
import pause
from click import UsageError
from clitt.core.term.cursor import cursor
from clitt.core.term.screen import screen
from clitt.core.term.terminal import terminal
from hspylib.core.config.path_object import PathObject
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import is_debugging, sysout
from hspylib.core.tools.text_tools import elide_text
from hspylib.modules.application.exit_status import ExitStatus
from hspylib.modules.application.version import Version
from hspylib.modules.eventbus.event import Event
from langchain_core.prompts import PromptTemplate

from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.askai_events import ASKAI_BUS_NAME, AskAiEvents, REPLY_ERROR_EVENT, REPLY_EVENT
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.commander.commander import ask_cli
from askai.core.component.audio_player import player
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.core.component.geo_location import geo_location
from askai.core.component.recorder import recorder
from askai.core.component.scheduler import scheduler
from askai.core.engine.ai_engine import AIEngine
from askai.core.engine.openai.temperature import Temperature
from askai.core.features.router import router
from askai.core.support.chat_context import ChatContext
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text, read_stdin
from askai.exception.exceptions import ImpossibleQuery, InaccurateResponse, MaxInteractionsReached, TerminatingQuery


class AskAi:
    """Responsible for the OpenAI functionalities."""

    SPLASH: str = classpath.get_resource("splash.txt").read_text(encoding=Charset.UTF_8.val)

    RE_ASKAI_CMD: str = r'^(?<!\\)/(\w+)( (.*))*$'

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
        query: str | List[str],
    ):
        self._interactive: bool = interactive
        self._ready: bool = False
        self._processing: Optional[bool] = None
        self._query_string: str | None = None
        self._question: str | None = None
        self._query_prompt: str | None = query_prompt
        self._engine: AIEngine = shared.create_engine(engine_name, model_name)
        self._context: ChatContext = shared.create_context(self._engine.ai_token_limit())
        # Setting configs from program args.
        self._get_query_string(interactive, query)
        configs.is_speak = not quiet
        configs.is_debug = is_debugging() or debug
        configs.tempo = tempo
        configs.is_interactive = interactive

    def __str__(self) -> str:
        device_info = f"{recorder.input_device[1]}" if recorder.input_device else ""
        device_info += f", AUTO-SWAP {'ON' if recorder.is_auto_swap else '%RED%OFF'}"
        dtm = f" {geo_location.datetime} "
        speak_info = str(configs.tempo) + ' @' + shared.engine.configs.tts_voice
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
    def cache_enabled(self) -> bool:
        return configs.is_cache

    @property
    def query_string(self) -> str:
        return self._query_string

    @property
    def question(self) -> str:
        return self._question

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
    def is_processing(self) -> bool:
        return self._processing

    @is_processing.setter
    def is_processing(self, processing: bool) -> None:
        if processing:
            self.reply(msg.wait())
        elif not processing and self._processing is not None and processing != self._processing:
            terminal.cursor.erase_line()
        self._processing = processing

    def run(self) -> None:
        """Run the program."""
        self._startup()
        if self.is_interactive:
            self._prompt()
        elif self.query_string:
            llm = lc_llm.create_chat_model(Temperature.CREATIVE_WRITING.temp)
            display_text(self.question, f"{shared.username}: ")
            if output := llm.invoke(self.query_string):
                self.reply(output.content)
                cache.save_query_history()
        else:
            display_text(f"%RED%Error: {msg.no_query_string()}%NC%")

    def reply(self, message: str) -> None:
        """Reply to the user with the AI response.
        :param message: The message to reply to the user.
        """
        if self.is_speak:
            self.engine.text_to_speech(message, f"{shared.nickname}: ")
        else:
            display_text(message, f"{shared.nickname}: ")

    def reply_error(self, message: str) -> None:
        """Reply API or system errors.
        :param message: The error message to be displayed.
        """
        log.error(message)
        if self.is_speak:
            self.engine.text_to_speech(f"Error: {message}", f"{shared.nickname}: ")
        else:
            display_text(f"Error: {message}", f"{shared.nickname}: ")

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
                if ev.args.erase_last:
                    cursor.erase_line()
                self.reply(ev.args.message)

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
        askai_bus = AskAiEvents.get_bus(ASKAI_BUS_NAME)
        askai_bus.subscribe(REPLY_EVENT, self._cb_reply_event)
        askai_bus.subscribe(REPLY_ERROR_EVENT, partial(self._cb_reply_event, error=True))
        if self.is_interactive:
            splash_thread: Thread = Thread(daemon=True, target=self._splash)
            splash_thread.start()
            nltk.download("averaged_perceptron_tagger", quiet=True, download_dir=CACHE_DIR)
            cache.set_cache_enable(self.cache_enabled)
            cache.read_query_history()
            player.start_delay()
            scheduler.start()
            recorder.setup()
            self._ready = True
            splash_thread.join()
            display_text(self, markdown=False)
            self.reply(msg.welcome(os.getenv("USER", "you")))
        else:
            recorder.setup()
            player.start_delay()
        log.info("AskAI is ready to use!")

    def _prompt(self) -> None:
        """Prompt for user interaction."""
        while query := shared.input_text(f"{shared.username}: ", f"Message {self.engine.nickname()}"):
            if not self._ask_and_reply(query):
                query = None
                break
            else:
                cache.save_query_history()
        if not query:
            self.reply(msg.goodbye())
        sysout("")

    def _ask_and_reply(self, question: str) -> bool:
        """Ask the question and provide the reply.
        :param question: The question to ask to the AI engine.
        """
        status = True
        try:
            if command := re.search(self.RE_ASKAI_CMD, question):
                args: list[str] = list(filter(
                    lambda a: a and a != 'None', re.split(r'\s', f"{command.group(1)} {command.group(2)}")
                ))
                ask_cli(args, standalone_mode=False)
            elif not (reply := cache.read_reply(question)):
                log.debug('Response not found for "%s" in cache. Querying from %s.', question, self.engine.nickname())
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.wait())
                if output := router.process(question):
                    self.reply(output)
            else:
                log.debug("Reply found for '%s' in cache.", question)
                self.reply(reply)
        except (NotImplementedError, ImpossibleQuery) as err:
            self.reply_error(str(err))
        except (MaxInteractionsReached, InaccurateResponse, ValueError) as err:
            self.reply_error(msg.unprocessable(str(err)))
        except UsageError as err:
            self.reply_error(msg.invalid_command(err))
        except TerminatingQuery:
            status = False

        return status

    def _get_query_string(self, interactive: bool, query_arg: str | list[str]) -> None:
        """Retrieve the proper query string used in the non interactive mode.
        :param interactive: The interactive mode.
        :param query_arg: The query argument provided by the command line.
        """
        query: str = str(" ".join(query_arg) if isinstance(query_arg, list) else query_arg)
        self._question = query
        dir_name, file_name = PathObject.split(self._query_prompt)
        if not interactive:
            stdin_args = read_stdin()
            template = PromptTemplate(
                input_variables=["context", "question"], template=prompt.read_prompt(file_name, dir_name)
            )
            final_prompt = template.format(context=stdin_args, question=self._question)
            self._query_string = final_prompt if query else stdin_args
            self._question = self._question or self._query_string
        else:
            self._query_string = query
