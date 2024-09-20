#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.openai
      @file: openai_configs.py
   @created: Fri, 12 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_configs import AskAiConfigs
from askai.core.askai_settings import settings
from hspylib.core.metaclass.singleton import Singleton
from typing import Literal


class OpenAiConfigs(AskAiConfigs, metaclass=Singleton):
    """Provides access to OpenAI configurations."""

    INSTANCE: "OpenAiConfigs"

    def __init__(self):
        super().__init__()
        self._stt_model = settings.get("askai.openai.speech.to.text.model")
        self._tts_model = settings.get("askai.openai.text.to.speech.model")
        self._tts_voice = settings.get("askai.openai.text.to.speech.voice")
        self._tts_format = settings.get("askai.openai.text.to.speech.audio.format")

    @property
    def stt_model(self) -> Literal["whisper-1"]:
        return self._stt_model

    @stt_model.setter
    def stt_model(self, value: Literal["whisper-1"]) -> None:
        self._stt_model = value

    @property
    def tts_model(self) -> Literal["tts-1", "tts-1-hd"]:
        return self._tts_model

    @tts_model.setter
    def tts_model(self, value: Literal["tts-1", "tts-1-hd"]) -> None:
        self._tts_model = value

    @property
    def tts_voice(self) -> Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
        return self._tts_voice

    @tts_voice.setter
    def tts_voice(self, value: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]) -> None:
        self._tts_voice = value

    @property
    def tts_format(self) -> Literal["mp3", "opus", "aac", "flac"]:
        return self._tts_format

    @tts_format.setter
    def tts_format(self, value: Literal["mp3", "opus", "aac", "flac"]) -> None:
        self._tts_format = value


assert OpenAiConfigs().INSTANCE is not None
