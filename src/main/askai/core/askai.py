#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core
      @file: askai.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import logging as log
import os
import sys
from functools import partial
from threading import Thread
from typing import List, Optional

import nltk
import pause
from clitt.core.term.cursor import cursor
from clitt.core.term.screen import screen
from clitt.core.term.terminal import terminal
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import sysout
from hspylib.modules.application.exit_status import ExitStatus
from hspylib.modules.eventbus.event import Event
from langchain_core.prompts import PromptTemplate

from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.askai_events import ASKAI_BUS_NAME, AskAiEvents, REPLY_ERROR_EVENT, REPLY_EVENT
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.audio_player import player
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.core.component.geo_location import geo_location
from askai.core.component.recorder import recorder
from askai.core.engine.ai_engine import AIEngine
from askai.core.model.chat_context import ChatContext
from askai.core.proxy.router import router
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text, read_stdin


class AskAi:
    """Responsible for the OpenAI functionalities."""

    SPLASH = classpath.get_resource("splash.txt").read_text(encoding=Charset.UTF_8.val)

    @staticmethod
    def _abort():
        """Abort the execution and exit."""
        sys.exit(ExitStatus.FAILED.val)

    def __init__(
        self, interactive: bool,
        is_speak: bool,
        tempo: int,
        engine_name: str,
        model_name: str,
        query: str | List[str]
    ):
        self._interactive: bool = interactive
        self._ready: bool = False
        self._processing: Optional[bool] = None
        self._query_string, self._question = None, None
        self._engine: AIEngine = shared.create_engine(engine_name, model_name)
        self._context: ChatContext = shared.create_context(self._engine.ai_token_limit())
        # Setting configs from program args.
        self._get_query_string(interactive, query)
        configs.is_speak = is_speak and interactive
        configs.tempo = tempo
        configs.is_interactive = interactive

    def __str__(self) -> str:
        device_info = f"{recorder.input_device[1].title()}" if recorder.input_device else ""
        return (
            f"%GREEN%"
            f"{'-=' * 40} %EOL%"
            f"     Engine: {self.engine} %EOL%"
            f"   Language: {configs.language} %EOL%"
            f"{'-+' * 40} %EOL%"
            f" Microphone: {device_info or '%RED%Undetected'} %GREEN%%EOL%"
            f"   Speaking: {'ON, tempo: ' + str(configs.tempo) if self.is_speak else '%RED%OFF'} %GREEN%%EOL%"
            f"    Caching: {'ON, TTL: ' + configs.ttl if cache.is_cache_enabled() else '%RED%OFF'} %GREEN%%EOL%"
            f"{'-=' * 40} %EOL%%NC%"
        )

    def _get_query_string(self, interactive: bool, query_arg: str | list[str]) -> None:
        """TODO"""
        query: str = str(" ".join(query_arg) if isinstance(query_arg, list) else query_arg)
        if not interactive:
            stdin_args = read_stdin()
            template = PromptTemplate(input_variables=[
                'os_type', 'shell', 'idiom', 'location', 'datetime', 'context', 'question'
            ], template=prompt.read_prompt('qstring-prompt'))
            self._question = query
            final_prompt = template.format(
                os_type=prompt.os_type, shell=prompt.shell, idiom=shared.idiom,
                location=geo_location.location, datetime=geo_location.datetime,
                context=stdin_args, question=self._question
            )
            self._query_string = final_prompt if query else stdin_args
        else:
            self._query_string = query

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
    def is_speak(self) -> bool:
        return configs.is_speak

    @property
    def is_processing(self) -> bool:
        return self._processing

    @property
    def is_interactive(self) -> bool:
        return self._interactive

    @is_processing.setter
    def is_processing(self, processing: bool) -> None:
        if processing:
            self.reply(msg.wait())
        elif not processing and self._processing is not None and processing != self._processing:
            terminal.cursor.erase_line()
        self._processing = processing

    def run(self) -> None:
        """Run the program."""
        if self.is_interactive:
            self._startup()
            self._prompt()
        elif self.query_string:
            llm = lc_llm.create_chat_model()
            display_text(self.question, f"{shared.username}: ")
            if output := llm.predict(self.query_string):
                display_text(output, f"{shared.nickname}: ")
                cache.save_query_history()
        else:
            display_text(msg.no_query_string())

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
            self.engine.text_to_speech(message, f"{shared.nickname}: ")
        else:
            display_text(message, f"{shared.nickname}: ")

    def _cb_reply_event(self, ev: Event, error: bool = False) -> None:
        """Callback to handle reply events."""
        if error:
            self.reply_error(ev.args.message)
        else:
            if ev.args.erase_last:
                cursor.erase_line()
            self.reply(ev.args.message)

    def _splash(self) -> None:
        """Display the AskAI splash screen."""
        splash_interval = 1000
        while not self._ready:
            if not self._processing:
                screen.clear()
                sysout(f"%GREEN%{self.SPLASH}%NC%")
            pause.milliseconds(splash_interval)
        pause.milliseconds(splash_interval * 2)
        screen.clear()

    def _startup(self) -> None:
        """Initialize the application."""
        splash_thread: Thread = Thread(daemon=True, target=self._splash)
        splash_thread.start()
        recorder.setup()
        nltk.download("averaged_perceptron_tagger", quiet=True, download_dir=CACHE_DIR)
        cache.set_cache_enable(self.cache_enabled)
        cache.read_query_history()
        askai_bus = AskAiEvents.get_bus(ASKAI_BUS_NAME)
        askai_bus.subscribe(REPLY_EVENT, self._cb_reply_event)
        askai_bus.subscribe(REPLY_ERROR_EVENT, partial(self._cb_reply_event, error=True))
        if configs.is_speak:
            player.start_delay()
        self._ready = True
        splash_thread.join()
        display_text(self, markdown=False)
        log.info("AskAI is ready to use!")
        self.reply(msg.welcome(os.getenv("USER", "you")))

    def _prompt(self) -> None:
        """Prompt for user interaction."""
        while query := shared.input_text(f"{shared.username}: "):
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
        if not (reply := cache.read_reply(question)):
            log.debug('Response not found for "%s" in cache. Querying from %s.', question, self.engine.nickname())
            status, output = router.process(question)
            if status:
                if output and output.response:
                    self.reply(output.response)
            else:
                self.reply_error(output.response)
        else:
            log.debug("Reply found for '%s' in cache.", question)
            self.reply(reply)
            status = True

        return status
