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
from threading import Thread
from typing import List, Optional

import pause
from clitt.core.term.cursor import Cursor
from clitt.core.term.screen import Screen
from clitt.core.term.terminal import Terminal
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import sysout
from hspylib.modules.application.exit_status import ExitStatus
from hspylib.modules.cli.keyboard import Keyboard
from hspylib.modules.eventbus.event import Event

from askai.__classpath__ import _Classpath
from askai.core.askai_configs import configs
from askai.core.askai_events import ASKAI_BUS_NAME, AskAiEvents, REPLY_EVENT
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.audio_player import AudioPlayer
from askai.core.component.cache_service import cache
from askai.core.component.recorder import recorder
from askai.core.engine.ai_engine import AIEngine
from askai.core.model.chat_context import ChatContext
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
from askai.core.processor.generic_processor import GenericProcessor
from askai.core.processor.internet_processor import InternetProcessor
from askai.core.processor.output_processor import OutputProcessor
from askai.core.processor.processor_proxy import proxy
from askai.core.processor.summary_processor import SummaryProcessor
from askai.core.support.object_mapper import object_mapper
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text


class AskAi:
    """Responsible for the OpenAI functionalities."""

    SPLASH = _Classpath.get_resource_path("splash.txt").read_text(encoding=Charset.UTF_8.val)

    @staticmethod
    def _abort():
        """Abort the execution and exit."""
        sys.exit(ExitStatus.FAILED.val)

    def __init__(
        self, interactive: bool, is_speak: bool, tempo: int, engine_name: str, model_name: str, query: str | List[str]
    ):
        self._interactive: bool = interactive
        self._ready: bool = False
        self._processing: Optional[bool] = None
        self._query_string: Optional[str] = str(" ".join(query) if isinstance(query, list) else query)
        self._engine: AIEngine = shared.create_engine(engine_name, model_name)
        self._context: ChatContext = shared.create_context(self._engine.ai_token_limit())
        # Setting configs from program args.
        configs.is_speak = is_speak
        configs.tempo = tempo

    def __str__(self) -> str:
        device_info = (" using " + recorder.input_device[1]) if recorder.input_device else ""
        return (
            f"%GREEN%"
            f"{'-=' * 40} %EOL%"
            f"     Engine: {self.engine.ai_name()} %EOL%"
            f"      Model: {self.engine.ai_model_name()} - {self.engine.ai_token_limit()}k tokens %EOL%"
            f"   Nickname: {self.engine.nickname()} %EOL%"
            f"   Language: {configs.language} %EOL%"
            f"{'--' * 40} %EOL%"
            f"Interactive: ON %EOL%"
            f"   Speaking: {'ON' if self.is_speak else 'OFF'}{device_info} %EOL%"
            f"    Caching: {'ON' if cache.is_cache_enabled() else 'OFF'} %EOL%"
            f"      Tempo: {configs.tempo} %EOL%"
            f"{'--' * 40} %EOL%%NC%"
        )

    @property
    def engine(self) -> AIEngine:
        return self._engine

    @property
    def context(self) -> ChatContext:
        return self._context

    @property
    def nickname(self) -> str:
        return f"  {self.engine.nickname()}"

    @property
    def username(self) -> str:
        return f"  {prompt.user.title()}"

    @property
    def cache_enabled(self) -> bool:
        return configs.is_cache

    @property
    def query_string(self) -> str:
        return self._query_string

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
            Terminal.INSTANCE.cursor.erase_line()
        self._processing = processing

    def run(self) -> None:
        """Run the program."""
        if self._interactive:
            self._startup()
            self._prompt()
        elif self.query_string:
            display_text(f"{self.username}: {self.query_string}%EOL%")
            self._ask_and_reply(self.query_string)

    def reply(self, message: str) -> None:
        """Reply to the user with the AI response.
        :param message: The message to reply to the user.
        """
        if self.is_speak:
            self.engine.text_to_speech(f"{self.nickname}: ", message)
        else:
            display_text(f"{self.nickname}: %GREEN%{message}%NC%")

    def reply_error(self, message: str) -> None:
        """Reply API or system errors.
        :param message: The error message to be displayed.
        """
        log.error(message)
        display_text(f"{self.nickname}: Error: {message or 'Aborted!'} %NC%")

    def _cb_reply_event(self, ev: Event) -> None:
        """Callback to handle reply events."""
        if ev.args.erase_last:
            Cursor.INSTANCE.erase_line()
        self.reply(ev.args.message)

    def _splash(self) -> None:
        """Display the AskAI splash screen."""
        splash_interval = 1000
        while not self._ready:
            if not self._processing:
                Screen.INSTANCE.clear()
                sysout(f"%GREEN%{self.SPLASH}%NC%")
            pause.milliseconds(splash_interval)
        pause.milliseconds(splash_interval * 2)
        Screen.INSTANCE.clear()

    def _startup(self) -> None:
        """Initialize the application."""
        splash_thread: Thread = Thread(daemon=True, target=self._splash)
        if configs.is_speak:
            recorder.setup()
            configs.is_speak = recorder.input_device is not None
        splash_thread.start()
        if configs.is_speak:
            AudioPlayer.INSTANCE.start_delay()
        cache.set_cache_enable(self.cache_enabled)
        cache.read_query_history()
        askai_bus = AskAiEvents.get_bus(ASKAI_BUS_NAME)
        askai_bus.subscribe(REPLY_EVENT, self._cb_reply_event)
        self._ready = True
        log.info("AskAI is ready !")
        splash_thread.join()
        display_text(self)
        self.reply(msg.welcome(os.getenv("USER", "you")))

    def _prompt(self) -> None:
        """Prompt for user interaction."""
        while query := self._input(f"{self.username}: "):
            if not self._ask_and_reply(query):
                query = None
                break
        if not query:
            self.reply(msg.goodbye())
        display_text("")

    def _input(self, __prompt: str) -> Optional[str]:
        """Prompt for user input.
        :param __prompt: The prompt to display to the user.
        """
        ret = None
        while ret is None:
            ret = line_input(__prompt)
            if ret == Keyboard.VK_CTRL_L:  # Use speech as input method.
                Terminal.INSTANCE.cursor.erase_line()
                spoken_text = self.engine.speech_to_text()
                if spoken_text:
                    display_text(f"{self.username}: {spoken_text}")
                    ret = spoken_text
            elif not isinstance(ret, str):
                display_text(f"{self.username}: %YELLOW%Speech-To-Text is disabled!%NC%", erase_last=True)
                ret = None

        return ret if not ret or isinstance(ret, str) else ret.val

    def _ask_and_reply(self, question: str) -> bool:
        """Ask the question and provide the reply.
        :param question: The question to ask to the AI engine.
        """
        if not (reply := cache.read_reply(question)):
            log.debug('Response not found for "%s" in cache. Querying from %s.', question, self.engine.nickname())
            status, response = proxy.process(question)
            if status:
                status = self._process_response(response)
            else:
                self.reply_error(response)
        else:
            log.debug('Reply found for "%s" in cache.', question)
            self.reply(reply)
            status = True
        return status

    def _process_response(self, proxy_response: QueryResponse) -> bool:
        """Process a query response using a processor that supports the query type."""
        status, output, q_type, processor = False, None, None, None
        # Intrinsic features
        if not proxy_response.intelligible:
            self.reply_error(msg.intelligible(proxy_response.question))
            return False
        elif proxy_response.terminating:
            log.info("User wants to terminate the conversation.")
            return False
        elif proxy_response.require_internet:
            log.info("Internet is required to fulfill the request.")
            processor = AIProcessor.get_by_name(InternetProcessor.__name__)
            processor.bind(AIProcessor.get_by_query_type(proxy_response.query_type))
        elif proxy_response.require_summarization:
            log.info("Summarization is required to fulfill the request.")
            processor = AIProcessor.get_by_name(SummaryProcessor.__name__)
            processor.bind(AIProcessor.get_by_name(GenericProcessor.__name__))
        # Query processors
        if processor or (q_type := proxy_response.query_type):
            if not processor and not (processor := AIProcessor.get_by_query_type(q_type)):
                log.error(f"Unable to find a proper processor for query type: {q_type}")
                self.reply_error(str(proxy_response))
                return False
            log.info("%s::Processing response for '%s'", processor, proxy_response.question)
            status, output = processor.process(proxy_response)
            if status and processor.next_in_chain():
                mapped_response = object_mapper.of_json(output, QueryResponse)
                if isinstance(mapped_response, QueryResponse):
                    self._process_response(mapped_response)
                else:
                    self.reply(str(mapped_response))
            elif status:
                self.reply(str(output))
            else:
                self.reply_error(str(output))
        else:
            self.reply_error(msg.invalid_response(proxy_response))

        return status
