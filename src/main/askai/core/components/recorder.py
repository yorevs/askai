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
import os
from pathlib import Path
from typing import Callable, List, Tuple

from clitt.core.term.terminal import Terminal
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.zoned_datetime import now_ms
from speech_recognition import AudioData, Recognizer, Microphone, UnknownValueError, RequestError

from askai.core.askai_messages import AskAiMessages
from askai.exception.exceptions import IntelligibleAudioError, InvalidRecognitionApiError
from askai.language.language import Language
from askai.utils.utilities import display_text

CACHE_DIR: Path = Path(f'{os.getenv("HHS_DIR", os.getenv("TEMP", "/tmp"))}/askai')

# Voice recordings directory.
REC_DIR: Path = Path(str(CACHE_DIR) + "/cache/recordings")
if not REC_DIR.exists():
    REC_DIR.mkdir(parents=True, exist_ok=True)


class Recorder(metaclass=Singleton):
    """Provide an interface to record voice using the microphone device."""

    INSTANCE = None

    class RecognitionApi(Enumeration):
        # fmt: off
        OPEN_AI = 'recognize_whisper'
        GOOGLE  = 'recognize_google'
        # fmt: on

    @staticmethod
    def get_device_list() -> List[Tuple[int, str]]:
        devices = []
        for index, name in enumerate(Microphone.list_microphone_names()):
            devices.append((index, name))
        return devices

    def __init__(self):
        self._rec: Recognizer = Recognizer()
        self._device_index = 1

    def listen(
        self,
        recognition_api: RecognitionApi = RecognitionApi.OPEN_AI,
        language: Language = Language.EN_US
    ) -> Tuple[Path, str]:
        """Listen to the microphone and save the AudioData as an mp3 file.
        """
        audio_path = Path(f"{REC_DIR}/askai-stt-{now_ms()}.wav")
        with Microphone(device_index=1) as source:
            try:
                self._detect_noise()
                display_text(AskAiMessages.INSTANCE.listening(), erase_last=True)
                audio: AudioData = self._rec.listen(source, 2, 5)
                display_text(AskAiMessages.INSTANCE.transcribing(), erase_last=True)
                with open(audio_path, "wb") as f_rec:
                    f_rec.write(audio.get_wav_data())
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
            finally:
                Terminal.INSTANCE.cursor.erase_line()

        return audio_path, stt_text

    def _detect_noise(self, interval: float = 1) -> None:
        """TODO"""
        with Microphone() as source:
            try:
                display_text(AskAiMessages.INSTANCE.noise_levels())
                self._rec.adjust_for_ambient_noise(source, duration=interval)
                Terminal.INSTANCE.cursor.erase_line()
            except UnknownValueError as err:
                raise IntelligibleAudioError(f"Unable to detect noise => {str(err)}") from err


assert Recorder().INSTANCE is not None
