#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: ai_engine.py
   @created: Fri, 5 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_configs import AskAiConfigs
from askai.core.engine.ai_model import AIModel
from askai.core.engine.ai_vision import AIVision
from askai.core.model.ai_reply import AIReply
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel, BaseLLM
from pathlib import Path
from typing import Optional, Protocol


class AIEngine(Protocol):
    """Provide an interface for AI engines."""

    def configs(self) -> AskAiConfigs:
        """Return the engine-specific configurations."""
        ...

    def nickname(self) -> str:
        """Get the AI engine nickname.
        :return: The nickname of the AI engine.
        """
        ...

    def models(self) -> list[AIModel]:
        """Get the list of available models for the engine.
        :return: A list of available AI models.
        """
        ...

    def voices(self) -> list[str]:
        """Return the available model voices for speech to text.
        :return: A list of available voices.
        """

    def vision(self) -> AIVision:
        """Return the engine's vision component.
        :return: The vision component of the engine.
        """
        ...

    def lc_model(self, temperature: float, top_p: float) -> BaseLLM:
        """Create a LangChain LLM model instance using the current AI engine.
        :param temperature: The LLM model temperature.
        :param top_p: The model engine top_p.
        :return: An instance of BaseLLM.
        """
        ...

    def lc_chat_model(self, temperature: float = 0.0) -> BaseChatModel:
        """Create a LangChain LLM chat model instance using the current AI engine.
        :param temperature: The LLM chat model temperature.
        :return: An instance of BaseChatModel.
        """
        ...

    def lc_embeddings(self, model: str) -> Embeddings:
        """Create a LangChain LLM embeddings model instance.
        :param model: The LLM embeddings model string.
        :return: An instance of BaseEmbeddingsModel.
        """
        ...

    def ai_name(self) -> str:
        """Get the AI engine name.
        :return: The name of the AI engine.
        """
        ...

    def ai_model_name(self) -> str:
        """Get the AI model name.
        :return: The name of the AI model.
        """
        ...

    def ai_token_limit(self) -> int:
        """Get the AI model token limit.
        :return: The token limit of the AI model.
        """
        ...

    def ask(self, chat_context: list[dict], temperature: float = 0.8, top_p: float = 0.0) -> AIReply:
        """Ask AI assistance for the given question and expect a response.
        :param chat_context: The chat history or context.
        :param temperature: The model engine temperature.
        :param top_p: The model engine top_p.
        :return: The AI's reply.
        """
        ...

    def text_to_speech(self, text: str, prefix: str = "", stream: bool = True, playback: bool = True) -> Optional[Path]:
        """Convert the provided text to speech.
        :param text: The text to convert to speech.
        :param prefix: The prefix of the streamed text.
        :param stream: Whether to stream the text into stdout.
        :param playback: Whether to play back the generated audio file.
        :return: The path to the generated audio file; or None if no file was generated.
        """
        ...

    def speech_to_text(self) -> Optional[str]:
        """Transcribe audio input from the microphone into text.
        :return: The transcribed text or None if transcription fails.
        """
        ...

    def calculate_tokens(self, text: str) -> int:
        """Calculate the number of tokens for the given text.
        :param text: The text for which to calculate tokens.
        :return: The number of tokens in the text.
        """
        ...
