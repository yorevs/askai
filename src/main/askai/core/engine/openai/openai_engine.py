#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.openai
      @file: openai_engine.py
   @created: Fri, 12 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

import logging as log
import os
from threading import Thread
from typing import List, Optional

import langchain_openai
import pause
from hspylib.core.preconditions import check_not_none
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel, BaseLLM
from openai import APIError, OpenAI

from askai.core.component.audio_player import AudioPlayer
from askai.core.component.cache_service import CacheService
from askai.core.component.recorder import Recorder
from askai.core.engine.openai.openai_configs import OpenAiConfigs
from askai.core.engine.openai.openai_model import OpenAIModel
from askai.core.model.ai_model import AIModel
from askai.core.model.ai_reply import AIReply
from askai.core.support.utilities import stream_text


class OpenAIEngine:
    """Provide a base class for OpenAI features. Implements the prototype AIEngine."""

    def __init__(self, model: AIModel = OpenAIModel.GPT_3_5_TURBO):
        super().__init__()
        self._model: AIModel = model
        self._configs: OpenAiConfigs = OpenAiConfigs.INSTANCE
        self._api_key: str = os.environ.get("OPENAI_API_KEY")
        self._client = OpenAI(api_key=self._api_key)

    def __str__(self):
        return f"{self.ai_name()} '{self.nickname()}' '{self._model}'"

    @property
    def url(self) -> str:
        return "https://api.openai.com/v1/chat/completions"

    @property
    def client(self) -> OpenAI:
        return self._client

    @property
    def configs(self) -> OpenAiConfigs:
        return self._configs

    def voices(self) -> list[str]:
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    def lc_model(self, temperature: float = 0.0, top_p: float = 0.0) -> BaseLLM:
        """Create a LangChain OpenAI llm model instance."""
        return langchain_openai.OpenAI(openai_api_key=self._api_key, temperature=temperature, top_p=top_p)

    def lc_chat_model(self, temperature: float = 0.0) -> BaseChatModel:
        """Create a LangChain OpenAI llm chat model instance."""
        return langchain_openai.ChatOpenAI(openai_api_key=self._api_key, temperature=temperature)

    def lc_embeddings(self) -> Embeddings:
        """Create a LangChain AI embeddings instance."""
        return langchain_openai.OpenAIEmbeddings(openai_api_key=self._api_key)

    def ai_name(self) -> str:
        """Get the AI model name."""
        return self.__class__.__name__

    def ai_model_name(self) -> str:
        """Get the AI model name."""
        return self._model.model_name()

    def ai_token_limit(self) -> int:
        """Get the AI model tokens limit."""
        return self._model.token_limit()

    def nickname(self) -> str:
        """Get the AI engine nickname."""
        return "ChatGPT"

    def models(self) -> List[AIModel]:
        """Get the list of available models for the engine."""
        return OpenAIModel.models()

    def ask(self, chat_context: List[dict], temperature: float = 0.8, top_p: float = 0.0) -> AIReply:
        """Ask AI assistance for the given question and expect a response.
        :param chat_context: The chat history or context.
        :param temperature: The model engine temperature.
        :param top_p: The model engine top_p.
        """
        try:
            check_not_none(chat_context)
            log.debug(f"Generating AI answer")
            response = self.client.chat.completions.create(
                model=self.ai_model_name(), messages=chat_context,
                temperature=temperature, top_p=top_p
            )
            reply = AIReply(response.choices[0].message.content, True)
            log.debug("Response received from LLM: %s", str(reply))
        except APIError as error:
            body: dict = error.body or {"message": "Message not provided"}
            reply = AIReply(f"%RED%{error.__class__.__name__} => {body['message']}%NC%", False)

        return reply

    def text_to_speech(self, text: str, prefix: str = "") -> None:
        """Text-T0-Speech the provided text.
        :param text: The text to speech.
        :param prefix: The prefix of the streamed text.
        """
        speech_file_path, file_exists = CacheService.get_audio_file(
            text, self._configs.tts_voice, self._configs.tts_format)
        if not file_exists:
            log.debug(f'Audio file "%s" not found in cache. Generating from %s.', self.nickname(), speech_file_path)
            response = self.client.audio.speech.create(
                input=text,
                model=self._configs.tts_model,
                voice=self._configs.tts_voice,
                response_format=self._configs.tts_format,
            )
            response.stream_to_file(speech_file_path)  # Save the audio file locally.
            log.debug(f"Audio file created: '%s' at %s", text, speech_file_path)
        else:
            log.debug(f"Audio file found in cache: '%s' at %s", text, speech_file_path)
        speak_thread = Thread(
            daemon=True, target=AudioPlayer.INSTANCE.play_audio_file, args=(speech_file_path, self._configs.tempo)
        )
        speak_thread.start()
        pause.seconds(AudioPlayer.INSTANCE.start_delay())
        stream_text(text, prefix)
        speak_thread.join()  # Block until the speech has finished.

    def speech_to_text(self) -> Optional[str]:
        """Transcribes audio input from the microphone into the text input language."""
        _, text = Recorder.INSTANCE.listen(language=self._configs.language)
        log.debug(f"Audio transcribed to: {text}")
        return text.strip()
