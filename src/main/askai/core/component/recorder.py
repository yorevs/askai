#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.components
      @file: recorder.py
   @created: Wed, 22 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import logging as log
from pathlib import Path
from typing import Callable, List, Tuple

from clitt.core.term.terminal import Terminal
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.zoned_datetime import now_ms
from speech_recognition import AudioData, Recognizer, Microphone, UnknownValueError, RequestError

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import AskAiMessages
from askai.core.component.cache_service import REC_DIR
from askai.exception.exceptions import IntelligibleAudioError, InvalidRecognitionApiError
from askai.language.language import Language


class Recorder(metaclass=Singleton):
    """Provide an interface to record voice using the microphone device."""

    INSTANCE: 'Recorder' = None

    class RecognitionApi(Enumeration):
        # fmt: off
        OPEN_AI = 'recognize_whisper'
        GOOGLE  = 'recognize_google'
        # fmt: on

    @classmethod
    def get_device_list(cls) -> List[Tuple[int, str]]:
        """Return a list of available devices."""
        devices = []
        for index, name in enumerate(Microphone.list_microphone_names()):
            devices.append((index, name))
        return devices

    def __init__(self):
        self._rec: Recognizer = Recognizer()
        self._devices = self.get_device_list() or []
        self._device_index = 0

    @property
    def devices(self) -> List[Tuple[int, str]]:
        return self._devices

    def select_device(self, index: int = 1) -> None:
        """Select an available device for recording."""
        self._device_index = index if len(self._devices) >= index else 0

    def listen(
        self,
        recognition_api: RecognitionApi = RecognitionApi.OPEN_AI,
        language: Language = Language.EN_US
    ) -> Tuple[Path, str]:
        """Listen to the microphone, save the AudioData as a wav file and then, transcribe the speech.
        :param recognition_api: the API to be used to recognize the speech.
        :param language: the spoken language.
        """
        audio_path = Path(f"{REC_DIR}/askai-stt-{now_ms()}.wav")
        with Microphone(device_index=self._device_index) as source:
            try:
                self._detect_noise()
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=AskAiMessages.INSTANCE.listening())
                audio: AudioData = self._rec.listen(source, phrase_time_limit=5)
                Terminal.INSTANCE.cursor.erase_line()
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=AskAiMessages.INSTANCE.transcribing(), erase_last=True)
                with open(audio_path, "wb") as f_rec:
                    f_rec.write(audio.get_wav_data())
                    log.debug("Voice recorded and saved as %s", audio_path)
                if api := getattr(self._rec, recognition_api.value):
                    log.debug("Recognizing voice using %s", recognition_api)
                    assert isinstance(api, Callable)
                    stt_text = api(audio, language=language.language)
                else:
                    raise InvalidRecognitionApiError(str(recognition_api or "<none>"))
            except UnknownValueError as err:
                raise IntelligibleAudioError(str(err)) from err
            except RequestError as err:
                raise InvalidRecognitionApiError(str(err)) from err

        return audio_path, stt_text

    def _detect_noise(self, interval: float = 1) -> None:
        """Detect and adjust the background noise level.
        :param interval: the interval in seconds of the noise detection.
        """
        with Microphone() as source:
            try:
                log.debug(AskAiMessages.INSTANCE.noise_levels())
                self._rec.adjust_for_ambient_noise(source, duration=interval)
            except UnknownValueError as err:
                raise IntelligibleAudioError(f"Unable to detect noise => {str(err)}") from err


assert Recorder().INSTANCE is not None
