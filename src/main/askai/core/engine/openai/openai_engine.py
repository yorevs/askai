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
from functools import partial
from threading import Thread
from typing import Callable, Optional, List

import pause
import speech_recognition as speech_rec
from hspylib.modules.cli.vt100.vt_color import VtColor
from openai import APIError, OpenAI, BadRequestError

from askai.core.askai_prompt import AskAiPrompt
from askai.core.engine.openai.openai_configs import OpenAiConfigs
from askai.core.engine.openai.openai_model import OpenAIModel
from askai.core.engine.openai.openai_reply import OpenAIReply
from askai.core.engine.protocols.ai_engine import AIEngine
from askai.core.engine.protocols.ai_model import AIModel
from askai.core.engine.protocols.ai_reply import AIReply
from askai.utils.cache_service import CacheService
from askai.utils.utilities import input_mic, play_audio_file, start_delay


class OpenAIEngine(AIEngine):
    """Provide a base class for OpenAI features. Implements the prototype AIEngine."""

    def __init__(self, model: AIModel = OpenAIModel.GPT_3_5_TURBO):
        super().__init__()
        self._nickname = "ChatGPT"
        self._url = "https://api.openai.com/v1/chat/completions"
        self._configs: OpenAiConfigs = OpenAiConfigs()
        self._prompts = AskAiPrompt.INSTANCE or AskAiPrompt()
        self._balance = 0
        self._model_name = model.model_name()
        self._chat_context = [{"role": "system", "content": self._prompts.setup()}]
        self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), organization=os.environ.get("OPENAI_ORG_ID"))

    @property
    def start_delay(self) -> float:
        return start_delay()

    @property
    def url(self):
        return self._url

    def ai_name(self) -> str:
        """Get the AI model name."""
        return self.__class__.__name__

    def ai_model(self) -> str:
        """Get the AI model name."""
        return self._model_name

    def nickname(self) -> str:
        """Get the AI engine nickname."""
        return self._nickname

    def models(self) -> List[AIModel]:
        """Get the list of available models for the engine."""
        return OpenAIModel.models()

    def ask(self, question: str) -> AIReply:
        """Ask AI assistance for the given question and expect a response.
        :param question: The question to send to the AI engine.
        """
        if not (reply := CacheService.read_reply(question)):
            log.debug('Response not found for: "%s" in cache. Querying AI engine.', question)
            try:
                self._chat_context.append({"role": "user", "content": question})
                log.debug(f"Generating AI answer for: {question}")
                response = self._client.chat.completions.create(
                    model=self._model_name, messages=self._chat_context,
                    temperature=0.0, top_p=0.0
                )
                reply = OpenAIReply(response.choices[0].message.content, True)
                self._chat_context.append({"role": "assistant", "content": reply.message})
                CacheService.save_reply(question, reply.message)
                CacheService.save_query_history()
            except APIError as error:
                body: dict = error.body or {"message": "Message not provided"}
                reply = OpenAIReply(f"%RED%{error.__class__.__name__} => {body['message']}%NC%", False)
                if isinstance(error, BadRequestError):
                    self.forget()
        else:
            log.debug('Response found for: "%s" in cache.', question)
            reply = OpenAIReply(reply, True)
            self._chat_context.append({"role": "user", "content": question})
            self._chat_context.append({"role": "assistant", "content": reply.message})

        return reply

    def forget(self) -> None:
        """Forget all of the chat context."""
        self._chat_context = [{"role": "system", "content": self._prompts.setup()}]

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
        speech_file_path, file_exists = CacheService.get_audio_file(text, self._configs.tts_format)
        if not file_exists:
            log.debug(f'Audio file "%s" not found in cache. Querying AI engine.', speech_file_path)
            response = self._client.audio.speech.create(
                input=VtColor.strip_colors(text),
                model=self._configs.tts_model,
                voice=self._configs.tts_voice,
                response_format=self._configs.tts_format,
            )
            response.stream_to_file(speech_file_path)  # Save the audio file locally.
        speak_thread = Thread(daemon=True, target=play_audio_file, args=(speech_file_path, speed))
        speak_thread.start()
        if cb_started:
            pause.seconds(self.start_delay)
            cb_started(text)
        speak_thread.join()  # Block until the speech has finished.
        if cb_finished:
            cb_finished()

    def speech_to_text(self, fn_listening: partial, fn_processing: partial) -> str:
        """Transcribes audio input from the microphone into the text input language.
        :param fn_listening: The function to display the listening message.
        :param fn_processing: The function to display the processing message.
        """
        text = input_mic(fn_listening, fn_processing, speech_rec.Recognizer.recognize_whisper)
        log.debug(f"Audio transcribed to: {text}")
        return text
