#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: ai_engine.py
   @created: Fri, 5 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
from typing import List, Protocol, Any, Optional

from askai.core.model.ai_model import AIModel
from askai.core.model.ai_reply import AIReply


class AIEngine(Protocol):
    """Provide an interface for AI engines."""

    def lc_model(self, **kwargs: Any) -> Any:
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

    def text_to_speech(self, prefix: str, text: str) -> None:
        """Text-T0-Speech the provided text.
        :param text: The text to speech.
        :param prefix: The prefix of the streamed text.
        """
        ...

    def speech_to_text(self) -> Optional[str]:
        """Transcribes audio input from the microphone into the text input language.
        """
        ...
