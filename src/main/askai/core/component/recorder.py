#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.components
      @file: recorder.py
   @created: Wed, 22 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.component.cache_service import REC_DIR
from askai.core.component.scheduler import Scheduler
from askai.core.support.utilities import display_text, seconds
from askai.exception.exceptions import InvalidInputDevice, InvalidRecognitionApiError
from askai.language.language import Language
from clitt.core.tui.mselect.mselect import mselect
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_argument, check_state
from hspylib.core.zoned_datetime import now_ms
from hspylib.modules.application.exit_status import ExitStatus
from pathlib import Path
from speech_recognition import AudioData, Microphone, Recognizer, RequestError, UnknownValueError, WaitTimeoutError
from typing import Callable, Optional, TypeAlias

import logging as log
import operator
import pause
import sys

InputDevice: TypeAlias = tuple[int, str]


class Recorder(metaclass=Singleton):
    """Provide an interface to record voice using the microphone device."""

    INSTANCE: "Recorder"

    class RecognitionApi(Enumeration):
        # fmt: off
        OPEN_AI = 'recognize_whisper'
        GOOGLE = 'recognize_google'
        # fmt: on

    @classmethod
    def get_device_list(cls) -> list[InputDevice]:
        """Return a list of available devices."""
        devices = []
        for index, name in enumerate(Microphone.list_microphone_names()):
            devices.append((index, name))
        return devices

    def __init__(self):
        self._rec: Recognizer = Recognizer()
        self._devices: list[InputDevice] = []
        self._device_index: int | None = None
        self._input_device: InputDevice | None = None
        self._old_device = None

    def setup(self) -> None:
        """Setup the recorder."""
        self._devices = self.get_device_list()
        log.debug("Available audio devices:\n%s", "\n".join([f"{d[0]} - {d[1]}" for d in self._devices]))
        self._select_device()

    @staticmethod
    @Scheduler.every(3000, 5000)
    def __device_watcher() -> None:
        """Watch for audio input devices being plugged/unplugged."""
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
    def devices(self) -> list[InputDevice]:
        return sorted(self._devices if self._devices else [], key=lambda x: x[0])

    @devices.setter
    def devices(self, value: list[InputDevice]) -> None:
        self._devices = value

    @property
    def input_device(self) -> Optional[InputDevice]:
        if self._input_device is not None:
            check_state(isinstance(self._input_device, tuple), "Input device is not a InputDevice")
        return self._input_device

    @property
    def device_index(self) -> Optional[int]:
        if self._device_index is not None:
            check_state(isinstance(self._device_index, int), "Device index is not a number")
        return self._device_index

    @property
    def is_auto_swap(self) -> bool:
        return configs.recorder_input_device_auto_swap

    def set_device(self, device: InputDevice) -> bool:
        """Test and set the specified device as current.
        :param device: rge device to set.
        """
        check_argument(device and isinstance(device, tuple), f"Invalid device: {device} -> {type(device)}")
        if ret := self.test_device(device[0]):
            log.info(msg.device_switch(str(device)))
            events.device_changed.emit(device=device)
            self._input_device = device
            self._device_index = device[0]
            configs.add_device(device[1])
        return ret

    def is_headphones(self) -> bool:
        """Whether the device is set is a headphone. This is a simplistic way of detecting it, bit it has been
        working so far."""
        return self.input_device is not None and self.input_device[0] > 1

    def listen(
        self,
        recognition_api: RecognitionApi = RecognitionApi.GOOGLE,  # FIXME Should default to OpenAI (SIGSEGV error)
        language: Language = Language.EN_US,
    ) -> tuple[Path, Optional[str]]:
        """listen to the microphone, save the AudioData as a wav file and then, transcribe the speech.
        :param recognition_api: the API to be used to recognize the speech.
        :param language: the spoken language.
        """
        audio_path = Path(f"{REC_DIR}/askai-stt-{now_ms()}.wav")
        with Microphone(device_index=self._device_index) as mic_source:
            try:
                self._detect_noise()
                events.listening.emit()
                audio: AudioData = self._rec.listen(
                    mic_source,
                    phrase_time_limit=seconds(configs.recorder_phrase_limit_millis),
                    timeout=seconds(configs.recorder_silence_timeout_millis),
                )
                stt_text = self._write_audio_file(audio, audio_path, language, recognition_api)
            except WaitTimeoutError as err:
                err_msg: str = msg.timeout(f"waiting for a speech input => '{err}'")
                log.warning("Timed out while waiting for a speech input!")
                events.reply_error.emit(message=err_msg, erase_last=True)
                stt_text = None
            except UnknownValueError as err:
                err_msg: str = msg.intelligible(err)
                log.warning("Speech was not intelligible!")
                events.reply_error.emit(message=err_msg, erase_last=True)
                stt_text = None
            except AttributeError as err:
                raise InvalidInputDevice(str(err)) from err
            except RequestError as err:
                raise InvalidRecognitionApiError(str(err)) from err
            finally:
                events.listening.emit(listening=False)

        return audio_path, stt_text

    def _write_audio_file(
        self, audio: AudioData, audio_path: str | Path, language: Language, recognition_api: RecognitionApi
    ) -> Optional[str]:
        """Write the audio file into disk."""

        with open(str(audio_path), "wb") as f_rec:
            f_rec.write(audio.get_wav_data())
            log.debug("Voice recorded and saved as %s", audio_path)
            if api := getattr(self._rec, recognition_api.value):
                events.reply.emit(message=msg.transcribing(), verbosity="debug", erase_last=True)
                log.debug("Recognizing voice using %s", recognition_api)
                assert isinstance(api, Callable)
                return api(audio, language=language.language)
            else:
                raise InvalidRecognitionApiError(str(recognition_api or "<none>"))
        return None

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
                err_msg: str = msg.intelligible(f"Unable to detect noise level => '{err}'")
                log.warning("Timed out while waiting for a speech input!")
                events.reply_error.emit(message=err_msg, erase_last=True)

    def _select_device(self) -> None:
        """Select device for recording."""
        available: list[str] = list(filter(lambda d: d, map(str.strip, configs.recorder_devices)))
        device: InputDevice | None = None
        devices: list[InputDevice] = list(reversed(self.devices))
        while not device:
            if available:
                for dev in devices:
                    if dev[1] in available and self.set_device(dev):
                        device = dev
                        break
            if not device:
                device: InputDevice = mselect(
                    devices, f"{'-=' * 40}%EOL%AskAI::Select the Audio Input device%EOL%{'=-' * 40}%EOL%"
                )
                if not device:
                    sys.exit(ExitStatus.FAILED.val)
                elif not self.set_device(device):
                    display_text(f"%HOM%%ED2%Error: '{device[1]}' is not an Audio Input device!%NC%")
                    devices.remove(device)
                    device = None
                    pause.seconds(2)


assert (recorder := Recorder().INSTANCE) is not None
