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
from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.component.cache_service import REC_DIR
from askai.core.support.settings import Settings
from askai.core.support.utilities import display_text
from askai.exception.exceptions import IntelligibleAudioError, InvalidInputDevice, InvalidRecognitionApiError
from askai.language.language import Language
from clitt.core.term.cursor import Cursor
from clitt.core.tui.mselect.mselect import mselect
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.core.zoned_datetime import now_ms
from pathlib import Path
from speech_recognition import AudioData, Microphone, Recognizer, RequestError, UnknownValueError, WaitTimeoutError
from typing import Callable, List, Optional, Tuple

import logging as log
import os
import pause


class Recorder(metaclass=Singleton):
    """Provide an interface to record voice using the microphone device."""

    INSTANCE: "Recorder" = None

    ASKAI_SETTINGS_DIR: str = f'{os.getenv("HHS_DIR", os.getenv("TEMP", "/tmp"))}'

    ASKAI_SETTINGS_FILE: str = ".askai.properties"

    class RecognitionApi(Enumeration):
        # fmt: off
        OPEN_AI = 'recognize_whisper'
        GOOGLE = 'recognize_google'
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
        self._settings: Settings = Settings(self.ASKAI_SETTINGS_FILE, load_dir=self.ASKAI_SETTINGS_DIR)
        self._devices = []
        self._device_index = None
        self._input_device = None
        self._rec_phrase_limit_s = 10
        self._rec_wait_timeout_s = 0.5

    def setup(self) -> None:
        """Setup the recorder."""
        self._devices = self.get_device_list()
        log.debug("Available audio devices:\n%s", "\n".join([f"{d[0]} - {d[1]}" for d in self._devices]))
        self._device_index = self._select_device()
        self._input_device = self._devices[self._device_index] if self._device_index is not None else None

    @property
    def devices(self) -> List[Tuple[int, str]]:
        return self._devices if self._devices else []

    @property
    def input_device(self) -> Optional[Tuple[int, str]]:
        return self._input_device if self._input_device else None

    def listen(
        self, recognition_api: RecognitionApi = RecognitionApi.OPEN_AI, language: Language = Language.EN_US
    ) -> Tuple[Path, Optional[str]]:
        """Listen to the microphone, save the AudioData as a wav file and then, transcribe the speech.
        :param recognition_api: the API to be used to recognize the speech.
        :param language: the spoken language.
        """
        audio_path = Path(f"{REC_DIR}/askai-stt-{now_ms()}.wav")
        with Microphone(device_index=self._device_index) as source:
            try:
                self._detect_noise()
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.listening())
                audio: AudioData = self._rec.listen(
                    source, phrase_time_limit=self._rec_phrase_limit_s, timeout=self._rec_wait_timeout_s
                )
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.transcribing(), erase_last=True)
                with open(audio_path, "wb") as f_rec:
                    f_rec.write(audio.get_wav_data())
                    log.debug("Voice recorded and saved as %s", audio_path)
                if api := getattr(self._rec, recognition_api.value):
                    log.debug("Recognizing voice using %s", recognition_api)
                    assert isinstance(api, Callable)
                    stt_text = api(audio, language=language.language)
                    Cursor.INSTANCE.erase_line()
                else:
                    raise InvalidRecognitionApiError(str(recognition_api or "<none>"))
            except WaitTimeoutError:
                log.warning("Timed out while waiting for a speech!")
                stt_text = ""
            except AttributeError as err:
                raise InvalidInputDevice(str(err)) from err
            except UnknownValueError as err:
                raise IntelligibleAudioError(str(err)) from err
            except RequestError as err:
                raise InvalidRecognitionApiError(str(err)) from err

        return audio_path, stt_text

    def _detect_noise(self, interval: float = 0.8) -> None:
        """Detect and adjust the background noise level.
        :param interval: the interval in seconds of the noise detection.
        """
        with Microphone() as source:
            try:
                log.debug("Adjusting noise levels…")
                self._rec.adjust_for_ambient_noise(source, duration=interval)
            except UnknownValueError as err:
                raise IntelligibleAudioError(f"Unable to detect noise => {str(err)}") from err

    def _select_device(self) -> Optional[int]:
        """Select device for recording."""
        done = False
        filepath: str = f"{self.ASKAI_SETTINGS_DIR}/{self.ASKAI_SETTINGS_FILE}"
        if not file_is_not_empty(filepath):
            self._settings.set("askai.recorder.devices", None)
            self._settings.set("askai.recorder.silence-timeout_ms", 1500)
            self._settings.set("askai.recorder.phrase.limit_ms", 0)
        available: List[str] = list(
            filter(lambda d: d, map(str.strip, eval(self._settings.get("askai.recorder.devices") or "[]")))
        )
        while not done:
            if available:
                for idx, device in self.devices:
                    if device in available and self._test_device(idx):
                        self._settings.save()
                        return idx
            # Choose device from list
            idx_device: Tuple[int, str] = mselect(
                self.devices, f"{'-=' * 40}%EOL%AskAI::Select the Input device%EOL%{'=-' * 40}%EOL%"
            )
            if not idx_device:
                break
            elif self._test_device(idx_device[0]):
                available.append(idx_device[1])
                self._settings.set("askai.recorder.devices", available)
                self._settings.save()
                return idx_device[0]

            display_text(f"%HOM%%ED2%Error:{idx_device[1]} does not support INPUTS !%NC%")
            self._devices.remove(idx_device)
            pause.seconds(2)

        return None

    def _test_device(self, idx: int) -> bool:
        """Test whether the input device specified by index can be used as an STT input.
        :param idx: The index of the device to be tested.
        """
        log.debug(f"Testing input device at index: %d", idx)
        try:
            with Microphone(device_index=idx) as source:
                self._rec.listen(source, timeout=0.5, phrase_time_limit=0.5)
                return True
        except WaitTimeoutError:
            log.info(f"Device: at index %d is functional!", idx)
            return True
        except (AssertionError, AttributeError):
            log.error(f"Device: at index %d is non functional!", idx)

        return False


assert (recorder := Recorder().INSTANCE) is not None
