#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.openai
      @file: openai_engine.py
   @created: Fri, 12 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import logging as log
import os
from threading import Thread
from typing import Callable, List, Any, Type

import pause
from hspylib.core.preconditions import check_not_none
from hspylib.modules.cli.vt100.vt_color import VtColor
from openai import APIError, OpenAI

from askai.core.component.audio_player import AudioPlayer
from askai.core.component.cache_service import CacheService
from askai.core.component.recorder import Recorder
from askai.core.engine.openai.openai_configs import OpenAiConfigs
from askai.core.engine.openai.openai_model import OpenAIModel
from askai.core.engine.openai.openai_reply import OpenAIReply
from askai.core.protocol.ai_engine import AIEngine
from askai.core.protocol.ai_model import AIModel
from askai.core.protocol.ai_reply import AIReply
from askai.utils.utilities import stream_text


class OpenAIEngine(AIEngine):
    """Provide a base class for OpenAI features. Implements the prototype AIEngine."""

    def __init__(self, model: AIModel = OpenAIModel.GPT_3_5_TURBO):
        super().__init__()
        self._model = model
        self._configs: OpenAiConfigs = OpenAiConfigs.INSTANCE
        self._api_key: str = os.environ.get("OPENAI_API_KEY")
        self._client = OpenAI(api_key=self._api_key)

    @property
    def url(self) -> str:
        return "https://api.openai.com/v1/chat/completions"

    @property
    def client(self) -> OpenAI:
        return self._client

    def lc_model(self, llm: Type, **kwargs: Any) -> Any:
        """Create a LangChain AI model instance.
        :param llm: The LangChain model Class type.
        """
        return llm(openai_api_key=self._api_key, **kwargs)

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

    def ask(self, chat_context: List, **kwargs: Any) -> AIReply:
        """Ask AI assistance for the given question and expect a response.
        :param chat_context: The chat history or context.
        """
        try:
            check_not_none(chat_context)
            log.debug(f"Generating AI answer")
            response = self.client.chat.completions.create(
                model=self.ai_model_name(), messages=chat_context,
                **kwargs
            )
            reply = OpenAIReply(response.choices[0].message.content, True)
        except APIError as error:
            body: dict = error.body or {"message": "Message not provided"}
            reply = OpenAIReply(f"%RED%{error.__class__.__name__} => {body['message']}%NC%", False)

        return reply

    def text_to_speech(self, text: str) -> None:
        """Text-T0-Speech the provided text.
        :param text: The text to speech.
        """
        speech_file_path, file_exists = CacheService.get_audio_file(text, self._configs.tts_format)
        if not file_exists:
            log.debug(f'Audio file "%s" not found in cache. Generating from %s.', self.nickname(), speech_file_path)
            response = self.client.audio.speech.create(
                input=VtColor.strip_colors(text),
                model=self._configs.tts_model,
                voice=self._configs.tts_voice,
                response_format=self._configs.tts_format,
            )
            response.stream_to_file(speech_file_path)  # Save the audio file locally.
            log.debug(f"Audio file created: '%s' at %s", text, speech_file_path)
        else:
            log.debug(f"Audio file found in cache: '%s' at %s", text, speech_file_path)
        speak_thread = Thread(
            daemon=True,
            target=AudioPlayer.INSTANCE.play_audio_file,
            args=(speech_file_path, self._configs.tempo)
        )
        speak_thread.start()
        pause.seconds(AudioPlayer.INSTANCE.start_delay())
        stream_text(text)
        speak_thread.join()  # Block until the speech has finished.

    def speech_to_text(self, fn_reply: Callable[[str], None]) -> str:
        """Transcribes audio input from the microphone into the text input language.
        :param fn_reply: The function to reply to the user using TTS.
        """
        _, text = Recorder.INSTANCE.listen(
            Recorder.RecognitionApi.OPEN_AI, fn_reply, self._configs.language
        )
        log.debug(f"Audio transcribed to: {text}")
        return text.strip()
