#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.components
      @file: recorder.py
   @created: Wed, 22 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

import logging as log
import operator
from pathlib import Path
from typing import Callable, Optional, Tuple

import pause
from clitt.core.term.cursor import cursor
from clitt.core.tui.mselect.mselect import mselect
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.zoned_datetime import now_ms
from speech_recognition import AudioData, Microphone, Recognizer, RequestError, UnknownValueError, WaitTimeoutError

from askai.core.askai_configs import configs
from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.component.cache_service import REC_DIR
from askai.core.component.scheduler import Scheduler
from askai.core.support.utilities import display_text, seconds
from askai.exception.exceptions import IntelligibleAudioError, InvalidInputDevice, InvalidRecognitionApiError
from askai.language.language import Language


class Recorder(metaclass=Singleton):
    """Provide an interface to record voice using the microphone device."""

    INSTANCE: "Recorder"

    class RecognitionApi(Enumeration):
        # fmt: off
        OPEN_AI = 'recognize_whisper'
        GOOGLE = 'recognize_google'
        # fmt: on

    @classmethod
    def get_device_list(cls) -> list[Tuple[int, str]]:
        """Return a list of available devices."""
        devices = []
        for index, name in enumerate(Microphone.list_microphone_names()):
            devices.append((index, name))
        return devices

    def __init__(self):
        self._rec: Recognizer = Recognizer()
        self._devices: list[tuple[int, str]] = []
        self._device_index = None
        self._input_device = None
        self._old_device = None

    def setup(self) -> None:
        """Setup the recorder."""
        self._devices = self.get_device_list()
        log.debug("Available audio devices:\n%s", "\n".join([f"{d[0]} - {d[1]}" for d in self._devices]))
        self._device_index = self._select_device()
        self._input_device = self._devices[self._device_index] if self._device_index is not None else None

    @staticmethod
    @Scheduler.every(2000, 10000)
    def __device_watcher() -> None:
        """Watch for device changes and swap if a new input device is found."""
        if recorder.is_auto_swap and recorder.devices:
            new_list = recorder.get_device_list()
            new_list.sort(key=operator.itemgetter(1))
            if len(recorder.devices) < len(new_list):
                new_devices = [d for d in new_list if d not in recorder.devices]
                for device in new_devices:
                    if recorder._test_device(device[0]):
                        log.info(msg.device_switch(str(device)))
                        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.device_switch(str(device)), erase_last=True)
                        recorder._input_device = device[0]
                        configs.add_device(device[1])
                        break
            elif len(recorder.devices) > len(new_list):
                for device in recorder.devices:
                    if recorder._test_device(device[0]):
                        log.info(msg.device_switch(str(device)))
                        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.device_switch(str(device)), erase_last=True)
                        recorder._input_device = device[0]
                        break
            recorder.devices = new_list

    @property
    def devices(self) -> list[Tuple[int, str]]:
        """TODO"""
        return self._devices if self._devices else []

    @devices.setter
    def devices(self, value: list[Tuple[int, str]]) -> None:
        self._devices = value

    @property
    def input_device(self) -> Optional[Tuple[int, str]]:
        """TODO"""
        return self._input_device if self._input_device else None

    @property
    def is_auto_swap(self) -> bool:
        """TODO"""
        return configs.recorder_input_device_auto_swap

    def listen(
        self,
        recognition_api: RecognitionApi = RecognitionApi.OPEN_AI,
        language: Language = Language.EN_US
    ) -> Tuple[Path, Optional[str]]:
        """listen to the microphone, save the AudioData as a wav file and then, transcribe the speech.
        :param recognition_api: the API to be used to recognize the speech.
        :param language: the spoken language.
        """
        audio_path = Path(f"{REC_DIR}/askai-stt-{now_ms()}.wav")
        with Microphone(device_index=self._device_index) as source:
            try:
                self._detect_noise()
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.listening())
                audio: AudioData = self._rec.listen(
                    source,
                    phrase_time_limit=seconds(configs.recorder_phrase_limit_millis),
                    timeout=seconds(configs.recorder_silence_timeout_millis))
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.transcribing(), erase_last=True)
                with open(audio_path, "wb") as f_rec:
                    f_rec.write(audio.get_wav_data())
                    log.debug("Voice recorded and saved as %s", audio_path)
                if api := getattr(self._rec, recognition_api.value):
                    log.debug("Recognizing voice using %s", recognition_api)
                    assert isinstance(api, Callable)
                    stt_text = api(audio, language=language.language)
                    cursor.erase_line()
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

    def _detect_noise(self) -> None:
        """Detect and adjust the background noise level."""
        with Microphone() as source:
            try:
                log.debug("Adjusting noise levels…")
                duration = seconds(configs.recorder_noise_detection_duration_millis)
                self._rec.adjust_for_ambient_noise(source, duration=duration)
            except UnknownValueError as err:
                raise IntelligibleAudioError(f"Unable to detect noise => {str(err)}") from err

    def _select_device(self) -> Optional[int]:
        """Select device for recording."""
        done = False
        available: list[str] = list(filter(lambda d: d, map(str.strip, configs.recorder_devices)))
        while not done:
            if available:
                for idx, device in reversed(self.devices):
                    if device in available and self._test_device(idx):
                        return idx
            # Choose device from list
            idx_device: Tuple[int, str] = mselect(
                self.devices, f"{'-=' * 40}%EOL%AskAI::Select the Input device%EOL%{'=-' * 40}%EOL%"
            )
            if not idx_device:
                break
            elif self._test_device(idx_device[0]):
                available.append(idx_device[1])
                configs.add_device(idx_device[1])
                return idx_device[0]

            display_text(f"%HOM%%ED2%Error:{idx_device[1]} does not support INPUTS !%NC%")
            self._devices.remove(idx_device)
            pause.seconds(2)

        return None

    def _test_device(self, idx: int) -> bool:
        """Test whether the input device specified by index can be used as an STT input.
        :param idx: The index of the device to be tested.
        """
        log.debug(f"Testing audio input device at index: '%d'", idx)
        test_timeout, test_phrase_limit = 0.5, 0.5
        try:
            with Microphone(device_index=idx) as source:
                self._rec.listen(source, timeout=test_timeout, phrase_time_limit=test_phrase_limit)
                return True
        except WaitTimeoutError:
            log.info(f"Device at index: '%d' is functional!", idx)
            return True
        except (AssertionError, AttributeError):
            log.warning(f"Device at index: '%d' is non functional!", idx)

        return False


assert (recorder := Recorder().INSTANCE) is not None
