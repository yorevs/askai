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
from typing import Callable, List, Protocol, Any, Type

from askai.core.protocol.ai_model import AIModel
from askai.core.protocol.ai_reply import AIReply


class AIEngine(Protocol):
    """Provide an interface for AI engines."""

    def lc_model(self, llm: Type, **kwargs: Any) -> Any:
        """Create a LangChain AI model instance."""

    def ai_name(self) -> str:
        """Get the AI engine name."""
        ...

    def ai_model_name(self) -> str:
        """Get the AI model name."""
        ...

    def ai_token_limit(self) -> int:
        """Get the AI model tokens limit."""
        ...

    def nickname(self) -> str:
        """Get the AI engine nickname."""
        ...

    def models(self) -> List[AIModel]:
        """Get the list of available models for the engine."""
        ...

    def ask(self, chat_context: List, **kwargs: Any) -> AIReply:
        """Ask AI assistance for the given question and expect a response.
        :param chat_context: The chat history or context.
        """
        ...

    def text_to_speech(self, text: str) -> None:
        """Text-T0-Speech the provided text.
        :param text: The text to speech.
        """
        """Text-T0-Speech the provided text.
        :param text: The text to speech.
        :param cb_started: The callback function called when the speaker starts.
        """
        ...

    def speech_to_text(
        self,
        fn_reply: Callable[[str], None]
    ) -> str:
        """Transcribes audio input from the microphone into the text input language.
        :param fn_reply: The function to reply to the user using TTS.
        """
        ...
