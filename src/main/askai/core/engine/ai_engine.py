#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: ai_engine.py
   @created: Fri, 5 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from typing import Any, List, Optional, Protocol

from langchain_core.language_models import BaseChatModel, BaseLLM

from askai.core.model.ai_model import AIModel
from askai.core.model.ai_reply import AIReply


class AIEngine(Protocol):
    """Provide an interface for AI engines."""

    def lc_model(self, temperature: float, top_p: float) -> BaseLLM:
        """Create a LangChain AI model instance.
        :param temperature: The model engine temperature.
        :param top_p: The model engine top_p.
        """
        ...

    def lc_chat_model(self, temperature: float = 0.0) -> BaseChatModel:
        """Create a LangChain OpenAI llm chat model instance.
        :param temperature: The model engine temperature.
        """
        ...

    def lc_embeddings(self) -> Any:
        """Create a LangChain AI embeddings instance."""
        ...

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

    def ask(self, chat_context: List[dict], temperature: float = 0.8, top_p: float = 0.0) -> AIReply:
        """Ask AI assistance for the given question and expect a response.
        :param chat_context: The chat history or context.
        :param temperature: The model engine temperature.
        :param top_p: The model engine top_p.
        """
        ...

    def text_to_speech(self, text: str, prefix: str = "") -> None:
        """Text-T0-Speech the provided text.
        :param text: The text to speech.
        :param prefix: The prefix of the streamed text.
        """
        ...

    def speech_to_text(self) -> Optional[str]:
        """Transcribes audio input from the microphone into the text input language."""
        ...

    def voices(self) -> list[str]:
        """Return the available model voices for speech to text."""
