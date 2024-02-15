#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.protocols
      @file: ai_engine.py
   @created: Fri, 5 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
from askai.core.engine.protocols.ai_model import AIModel
from askai.core.engine.protocols.ai_reply import AIReply
from functools import partial
from typing import Callable, List, Optional, Protocol


class AIEngine(Protocol):
    """Provide an interface for AI engines."""

    def ai_name(self) -> str:
        """Get the AI engine name."""
        ...

    def ai_model(self) -> str:
        """Get the AI model name."""
        ...

    def nickname(self) -> str:
        """Get the AI engine nickname."""
        ...

    def models(self) -> List[AIModel]:
        """Get the list of available models for the engine."""
        ...

    def ask(self, question: str) -> AIReply:
        """Ask AI assistance for the given question and expect a response.
        :param question: The question to send to the AI engine.
        """
        ...

    def forget(self) -> None:
        """Forget the chat context and start over."""
        ...

    def text_to_speech(
        self,
        text: str = None,
        speed: int = 0,
        cb_started: Optional[Callable[[str], None]] = None,
        cb_finished: Optional[Callable] = None,
    ) -> None:
        """Text-T0-Speech the provided text.
        :param text: The text to speech.
        :param speed: The tempo to play the generated audio [1..3].
        :param cb_started: The callback function called when the speaker starts.
        :param cb_finished: The callback function called when the speaker ends.
        """
        ...

    def speech_to_text(self, fn_listening: partial, fn_processing: partial) -> str:
        """Transcribes audio input from the microphone into the text input language.
        :param fn_listening: The function to display the listening message.
        :param fn_processing: The function to display the processing message.
        """
        ...
