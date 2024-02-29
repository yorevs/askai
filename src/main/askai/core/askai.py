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
from clitt.core.term.screen import Screen
from clitt.core.term.terminal import Terminal
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import sysout
from hspylib.modules.application.exit_status import ExitStatus
from hspylib.modules.cli.keyboard import Keyboard

from askai.__classpath__ import _Classpath
from askai.core.askai_configs import AskAiConfigs
from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.component.audio_player import AudioPlayer
from askai.core.component.cache_service import CacheService
from askai.core.component.object_mapper import ObjectMapper
from askai.core.component.recorder import Recorder
from askai.core.model.chat_context import ChatContext
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor
from askai.core.protocol.ai_engine import AIEngine
from askai.language.language import Language
from askai.utils.utilities import display_text


class AskAi:
    """Responsible for the OpenAI functionalities."""

    MSG = AskAiMessages.INSTANCE

    SPLASH = _Classpath.get_resource_path("splash.txt").read_text(encoding=Charset.UTF_8.val)

    @staticmethod
    def _abort():
        """Abort the execution and exit."""
        sys.exit(ExitStatus.FAILED.val)

    def __init__(
        self,
        interactive: bool,
        is_speak: bool,
        tempo: int,
        engine: AIEngine,
        query_string: str | List[str],
    ):
        self._configs: AskAiConfigs = AskAiConfigs.INSTANCE
        self._interactive: bool = interactive
        self._engine: AIEngine = engine
        self._query_string: str = str(" ".join(query_string) if isinstance(query_string, list) else query_string)
        self._ready: bool = False
        self._processing: bool | None = None
        self._chat_context = ChatContext(self.token_limit)
        # Setting configs from program args.
        self._configs.is_speak = is_speak
        self._configs.tempo = tempo

    def __str__(self) -> str:
        return (
            f"%GREEN%"
            f"{'-=' * 40} %EOL%"
            f"     Engine: {self._engine.ai_name()} %EOL%"
            f"      Model: {self._engine.ai_model_name()} - {self._engine.ai_token_limit()} tokens %EOL%"
            f"   Nickname: {self._engine.nickname()} %EOL%"
            f"{'--' * 40} %EOL%"
            f"   Language: {self.language.name} %EOL%"
            f"Interactive: ON %EOL%"
            f"   Speaking: {'ON' if self.is_speak else 'OFF'} %EOL%"
            f"    Caching: {'ON' if CacheService.is_cache_enabled() else 'OFF'} %EOL%"
            f"      Tempo: {self.stream_speed} %EOL%"
            f"{'--' * 40} %EOL%%NC%"
        )

    @property
    def username(self) -> str:
        return f"  {os.getenv('USER', 'you').title()}"

    @property
    def nickname(self) -> str:
        return f"  {self._engine.nickname()}"

    @property
    def model(self) -> str:
        return self._engine.ai_model_name()

    @property
    def token_limit(self) -> int:
        return self._engine.ai_token_limit()

    @property
    def cache_enabled(self) -> bool:
        return self._configs.is_cache

    @property
    def query_string(self) -> str:
        return self._query_string

    @property
    def stream_speed(self) -> int:
        return self._configs.tempo

    @property
    def is_speak(self) -> bool:
        return self._configs.is_speak

    @property
    def language(self) -> Language:
        return self._configs.language

    @property
    def is_processing(self) -> bool:
        return self._processing

    @is_processing.setter
    def is_processing(self, processing: bool) -> None:
        if processing:
            self._reply(self.MSG.wait())
        elif not processing and self._processing is not None and processing != self._processing:
            Terminal.INSTANCE.cursor.erase_line()
        self._processing = processing

    def run(self) -> None:
        """Run the program."""
        if self._interactive:
            self._startup()
            self._prompt()
        elif self._query_string:
            display_text(f"{self.username}: {self._query_string}%EOL%")
            self._ask_and_reply(self._query_string)

    def _splash(self) -> None:
        """Display the AskAI splash screen."""
        Screen.INSTANCE.clear()
        sysout(f"%GREEN%{self.SPLASH}%NC%")
        while not self._ready:
            pause.milliseconds(500)
        pause.seconds(1)
        Screen.INSTANCE.clear()

    def _startup(self) -> None:
        """Initialize the application."""
        splash_thread: Thread = Thread(
            daemon=True, target=self._splash
        )
        splash_thread.start()
        CacheService.set_cache_enable(self.cache_enabled)
        CacheService.read_query_history()
        if self.is_speak:
            AudioPlayer.INSTANCE.start_delay()
            log.debug(
                "Available audio devices:\n%s",
                "\n".join([f"{d[0]} - {d[1]}" for d in Recorder.INSTANCE.devices])
            )
        self._ready = True
        log.info("AskAI is ready !")
        splash_thread.join()
        display_text(self)
        self._reply(self.MSG.welcome(os.getenv('USER', 'you')))

    def _prompt(self) -> None:
        """Prompt for user interaction."""
        while query := self._input(f"{self.username}: "):
            if not self._ask_and_reply(query):
                query = None
                break
        if not query:
            self._reply(self.MSG.goodbye())
        display_text("")

    def _input(self, prompt: str) -> Optional[str]:
        """Prompt for user input.
        :param prompt: The prompt to display to the user.
        """
        ret = None
        while ret is None:
            ret = line_input(prompt)
            if self.is_speak and ret == Keyboard.VK_CTRL_L:  # Use speech as input method.
                Terminal.INSTANCE.cursor.erase_line()
                spoken_text = self._engine.speech_to_text(self._reply)
                if spoken_text:
                    display_text(f"{self.username}: {spoken_text}")
                    ret = spoken_text
            elif not self.is_speak and not isinstance(ret, str):
                display_text(f"{self.username}: %YELLOW%Speech-To-Text is disabled!%NC%", erase_last=True)
                ret = None

        return ret if not ret or isinstance(ret, str) else ret.val

    def _ask_and_reply(self, question: str) -> bool:
        """Ask the question and provide the reply.
        :param question: The question to ask to the AI engine.
        """
        if not (reply := CacheService.read_reply(question)):
            log.debug('Response not found for "%s" in cache. Querying from %s.', question, self._engine.nickname())
            self.is_processing = True
            context = self._chat_context.set("SETUP", AskAiPrompt.INSTANCE.setup(question), 'user')
            if (response := self._engine.ask(context)) and response.is_success():
                self.is_processing = False
                query_response = ObjectMapper.INSTANCE.of_json(response.reply_text(), QueryResponse)
                log.debug("Received a query_response for '%s' -> %s", question, query_response)
                self._process_response(query_response)
            else:
                self.is_processing = False
                self._reply_error(response.reply_text())
        else:
            log.debug('Reply found for "%s" in cache.', question)
            self._reply(reply)
        return True

    def _reply(self, message: str) -> None:
        """Reply to the user with the AI response.
        :param message: The message to reply to the user.
        """
        display_text(f"{self.nickname}: ", end="")
        if self.is_speak:
            self._engine.text_to_speech(message)
        else:
            display_text(message)

    def _reply_error(self, error_message: str) -> None:
        """Reply API or system errors.
        :param error_message: The error message to be displayed.
        """
        display_text(f"%RED%{self.nickname}: {error_message}%NC%")

    def _process_response(self, query_response: QueryResponse) -> bool:
        """Process a query response using a processor that supports the query type."""
        if not query_response.intelligible:
            self._reply_error(self.MSG.intelligible())
        elif query_response.terminating:
            log.info("User wants to terminate the conversation.")
        elif query_response.query_type:
            processor: AIProcessor = AIProcessor.get_processor(query_response.query_type)
            log.info("Using processor %s to process the response.", processor)
            status, output = processor.process(query_response)
            self._reply(output) if status else self._reply_error(output)
            return status
        else:
            self._reply_error(f"Unknown query type: %EOL%{query_response}%EOL%")

        return False
