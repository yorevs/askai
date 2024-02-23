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
import re
import sys
from functools import partial
from shutil import which
from threading import Thread
from typing import List, Optional, Any

import pause
from clitt.core.term.screen import Screen
from clitt.core.term.terminal import Terminal
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.enums.charset import Charset
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import sysout
from hspylib.core.tools.text_tools import ensure_endswith
from hspylib.modules.application.exit_status import ExitStatus

from askai.__classpath__ import _Classpath
from askai.core.askai_configs import AskAiConfigs
from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.components.audio_player import AudioPlayer
from askai.core.components.recorder import Recorder
from askai.core.engine.protocols.ai_engine import AIEngine
from askai.language.language import Language
from askai.utils.cache_service import CacheService
from askai.utils.constants import Constants
from askai.utils.utilities import stream_text, display_text


class AskAi(metaclass=Singleton):
    """Responsible for the OpenAI functionalities."""

    INSTANCE = None

    MSG = AskAiMessages.INSTANCE

    SPLASH = _Classpath.get_resource_path("splash.txt").read_text(encoding=Charset.UTF_8.val)

    @staticmethod
    def _abort():
        """Abort the execution and exit."""
        sys.exit(ExitStatus.FAILED.val)

    def __init__(
        self,
        interactive: bool,
        is_stream: bool,
        is_speak: bool,
        tempo: int,
        engine: AIEngine,
        query_string: str | List[str],
    ):
        self._configs: AskAiConfigs = AskAiConfigs.INSTANCE
        self._prompts = AskAiPrompt.INSTANCE
        self._interactive: bool = interactive
        self._engine: AIEngine = engine
        self._query_string: str = str(" ".join(query_string) if isinstance(query_string, list) else query_string)
        self._done: bool = False
        self._ready: bool = False
        self._processing: bool | None = None
        self._cmd_num = 0
        self._query_num = 0
        self._configs.is_stream = is_stream
        self._configs.is_speak = is_speak
        self._configs.tempo = tempo
        self.MSG.llm = self.llm

    def __str__(self) -> str:
        return (
            f"%GREEN%"
            f"{'-=' * 40} %EOL%"
            f"     Engine: {self._engine.ai_name()} %EOL%"
            f"      Model: {self._engine.ai_model()} %EOL%"
            f"   Nickname: {self._engine.nickname()} %EOL%"
            f"{'--' * 40} %EOL%"
            f"   Language: {self.language.name} %EOL%"
            f"Interactive: ON %EOL%"
            f"  Streaming: {'ON' if self.is_stream else 'OFF'} %EOL%"
            f"   Speaking: {'ON' if self.is_speak else 'OFF'} %EOL%"
            f"    Caching: {'ON' if CacheService.is_cache_enabled() else 'OFF'} %EOL%"
            f"      Tempo: {self.stream_speed} %EOL%"
            f"{'--' * 40} %EOL%%NC%"
        )

    @property
    def user(self) -> str:
        return f"%EL0% {os.getenv('USER', 'you').title()}"

    @property
    def llm(self) -> str:
        return f"%EL0% {self._engine.nickname()}"

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
    def is_stream(self) -> bool:
        return self._configs.is_stream

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
            if not re.match(Constants.TERM_EXPRESSIONS, self._query_string.lower()):
                display_text(f"{self.user}: {self._query_string}%EOL%")
                self._ask_and_reply(self._query_string)

    def _splash(self) -> None:
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

    def _stream_text(self, text: Any) -> None:
        """Stream the message using default parameters.
        :param text: The message to be streamed.
        """
        display_text(f"{self.llm}: ", end="")
        stream_text(text)

    def _prompt(self) -> None:
        """Prompt for user interaction."""
        while query := self._input(f"{self.user}: "):
            if not query:
                continue
            elif re.match(Constants.TERM_EXPRESSIONS, query.lower()):
                self._reply(self.MSG.goodbye())
                break
            else:
                self._ask_and_reply(query)
        if not query:
            self._reply(self.MSG.goodbye())
        display_text("")

    def _input(self, prompt: str) -> Optional[str]:
        """Prompt for user input.
        :param prompt: The prompt to display to the user.
        """
        ret = line_input(prompt)
        if self.is_speak and ret == Constants.PUSH_TO_TALK:  # Use audio as input method.
            Terminal.INSTANCE.cursor.erase_line()
            spoken_text = self._engine.speech_to_text(
                partial(self._reply, self.MSG.listening()),
                partial(self._reply, self.MSG.transcribing())
            )
            if spoken_text:
                display_text(f"{self.user}: {spoken_text}")
                ret = spoken_text
        elif not self.is_speak and not isinstance(ret, str):
            display_text(f"{self.user}: %YELLOW%Speech-To-Text is disabled!%NC%", erase_last=True)
            ret = None

        return ret if not ret or isinstance(ret, str) else ret.val

    def _reply(self, reply_message: str, speak: bool = True) -> str:
        """Reply to the user with the AI response.
        :param reply_message: The message to reply to the user.
        :param speak: Whether to speak the reply or not.
        """
        if self.is_stream and speak and self.is_speak:
            self._engine.text_to_speech(reply_message, self._configs.tempo, cb_started=self._stream_text)
        elif not self.is_stream and speak and self.is_speak:
            self._engine.text_to_speech(reply_message, self._configs.tempo, cb_started=display_text)
        elif self.is_stream:
            self._stream_text(reply_message)
        else:
            display_text(f"{self.llm}: {reply_message}")

        return reply_message

    def _reply_error(self, error_message: str) -> None:
        """Reply API or system errors.
        :param error_message: The error message to be displayed.
        """
        display_text(f"{self.llm}: {ensure_endswith(error_message, os.linesep)}")

    def _ask_and_reply(self, query: str) -> None:
        """Ask the question and provide the reply.
        :param query: The question to ask to the AI engine.
        """
        self.is_processing = True
        if (response := self._engine.ask(query)) and response.is_success():
            self.is_processing = False
            if (reply := response.reply_text()) and (
                mat := re.match(r".*`{3}(bash|zsh)(.+)`{3}.*", reply.strip().replace("\n", ""), re.I | re.M)
            ):
                self._process_command(mat.group(2))
            else:
                self._reply(reply)
        else:
            self.is_processing = False
            self._reply_error(response.reply_text())

    def _process_command(self, cmd_line: str) -> None:
        """Attempt to process command.
        :param cmd_line: The command line to execute.
        """
        if (command := cmd_line.split(" ")[0]) and which(command):
            cmd_line = cmd_line.replace("~", os.getenv("HOME"))
            self._reply(self.MSG.executing())
            log.info("Processing command `%s'", cmd_line)
            output, exit_code = Terminal.INSTANCE.shell_exec(cmd_line, shell=True)
            if exit_code == ExitStatus.SUCCESS:
                self._reply(self.MSG.cmd_success(exit_code))
                if output:
                    self._ask_and_reply(f"%COMMAND OUTPUT: \n\n{output}")
                else:
                    self._reply(self.MSG.cmd_no_output())
            else:
                self._reply(self.MSG.cmd_failed(command))
        else:
            self._reply(self.MSG.cmd_no_exist(command))
