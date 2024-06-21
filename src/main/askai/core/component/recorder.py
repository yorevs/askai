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
from typing import Callable, Optional, TypeAlias

from askai.core.askai_configs import configs
from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.component.cache_service import REC_DIR
from askai.core.component.scheduler import Scheduler
from askai.core.support.utilities import display_text, seconds
from askai.exception.exceptions import IntelligibleAudioError, InvalidInputDevice, InvalidRecognitionApiError
from askai.language.language import Language
from clitt.core.term.cursor import cursor
from clitt.core.tui.mselect.mselect import mselect
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_state, check_argument
from hspylib.core.zoned_datetime import now_ms
from speech_recognition import AudioData, Microphone, Recognizer, RequestError, UnknownValueError, WaitTimeoutError

DeviceType: TypeAlias = tuple[int, str]


class Recorder(metaclass=Singleton):
    """Provide an interface to record voice using the microphone device."""

    INSTANCE: "Recorder"

    class RecognitionApi(Enumeration):
        # fmt: off
        OPEN_AI = 'recognize_whisper'
        GOOGLE  = 'recognize_google'
        # fmt: on

    @classmethod
    def get_device_list(cls) -> list[DeviceType]:
        """Return a list of available devices."""
        devices = []
        for index, name in enumerate(Microphone.list_microphone_names()):
            devices.append((index, name))
        return devices

    def __init__(self):
        self._rec: Recognizer = Recognizer()
        self._devices: list[DeviceType] = []
        self._device_index: int | None = None
        self._input_device: DeviceType | None = None
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
                new_devices = [dev for dev in new_list if dev not in recorder.devices]
                for device in new_devices:
                    if recorder.set_device(device):
                        break
            elif len(recorder.devices) > len(new_list):
                for device in recorder.devices:
                    if recorder.set_device(device):
                        break
            recorder.devices = new_list

    @property
    def devices(self) -> list[DeviceType]:
        return sorted(self._devices if self._devices else [], key=lambda x: x[0])

    @devices.setter
    def devices(self, value: list[DeviceType]) -> None:
        self._devices = value

    @property
    def input_device(self) -> Optional[DeviceType]:
        if self._input_device is not None:
            check_state(isinstance(self._input_device, tuple), "Input device is not a DeviceType")
        return self._input_device if self._input_device else None

    @property
    def device_index(self) -> Optional[int]:
        if self._device_index is not None:
            check_state(isinstance(self._device_index, int), "Device index is not a number")
        return self._device_index if self._device_index else None

    @property
    def is_auto_swap(self) -> bool:
        return configs.recorder_input_device_auto_swap

    def set_device(self, device: DeviceType) -> bool:
        """Set device as current."""
        check_argument(device is not None and isinstance(device, tuple), f"Invalid device: {device}")
        if ret := self.test_device(device[0]):
            log.info(msg.device_switch(str(device)))
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.device_switch(str(device)), erase_last=True)
            self._input_device = device
            self._device_index = device[0]
            configs.add_device(device[1])
        return ret

    def listen(
        self,
        recognition_api: RecognitionApi = RecognitionApi.GOOGLE,
        language: Language = Language.EN_US
    ) -> tuple[Path, Optional[str]]:
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

    def test_device(self, idx: int) -> bool:
        """Test whether the input device specified by index can be used as an STT input.
        :param idx: The index of the device to be tested.
        """
        log.debug(f"Testing audio input device at index: '%d'", idx)
        test_timeout, test_phrase_limit = 0.3, 0.3
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
                    if device in available and self.test_device(idx):
                        return idx
            idx_device: DeviceType = mselect(
                self.devices, f"{'-=' * 40}%EOL%AskAI::Select the Input device%EOL%{'=-' * 40}%EOL%")
            if not idx_device:
                break
            elif self.test_device(idx_device[0]):
                available.append(idx_device[1])
                configs.add_device(idx_device[1])
                return idx_device[0]

            display_text(f"%HOM%%ED2%Error:{idx_device[1]} does not support INPUTS !%NC%")
            self._devices.remove(idx_device)
        return None


assert (recorder := Recorder().INSTANCE) is not None
