#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.askai_configs
      @file: askai_configs.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import locale
import os
from shutil import which

from hspylib.core.enums.charset import Charset
from hspylib.core.metaclass.singleton import Singleton

from askai.__classpath__ import classpath
from askai.core.askai_settings import settings
from askai.language.language import Language


class AskAiConfigs(metaclass=Singleton):
    """Provides access to AskAI configurations."""

    INSTANCE: "AskAiConfigs"

    # The resources folder
    RESOURCE_DIR = str(classpath.resource_path())

    def __init__(self):
        self._recorder_devices: set[str] = set(map(str.strip, settings.get_list("askai.recorder.devices")))

    @property
    def engine(self) -> str:
        return settings.get("askai.default.engine")

    @engine.setter
    def engine(self, value: str) -> None:
        settings.put("askai.default.engine", value)

    @property
    def model(self) -> str:
        return settings.get("askai.default.engine.model")

    @model.setter
    def model(self, value: str) -> None:
        settings.put("askai.default.engine.model", value)

    @property
    def is_interactive(self) -> bool:
        return settings.get_bool("askai.interactive.enabled")

    @is_interactive.setter
    def is_interactive(self, value: bool) -> None:
        settings.put("askai.interactive.enabled", value)

    @property
    def is_speak(self) -> bool:
        return which("ffplay") and settings.get_bool("askai.speak.enabled")

    @is_speak.setter
    def is_speak(self, value: bool) -> None:
        settings.put("askai.speak.enabled", which("ffplay") and not self.is_debug and value)

    @property
    def is_debug(self) -> bool:
        return settings.get_bool("askai.debug.enabled")

    @is_debug.setter
    def is_debug(self, value: bool) -> None:
        settings.put("askai.debug.enabled", value)

    @property
    def is_cache(self) -> bool:
        return settings.get_bool("askai.cache.enabled")

    @is_cache.setter
    def is_cache(self, value: bool) -> None:
        settings.put("askai.cache.enabled", value)

    @property
    def tempo(self) -> int:
        return settings.get_int("askai.text.to.speech.tempo")

    @tempo.setter
    def tempo(self, value: int) -> None:
        settings.put("askai.text.to.speech.tempo", value)

    @property
    def ttl(self) -> int:
        return settings.get_int("askai.cache.ttl.minutes")

    @ttl.setter
    def ttl(self, value: int) -> None:
        settings.put("askai.cache.ttl.minutes", value)

    @property
    def chunk_size(self) -> int:
        return settings.get_int("askai.text.splitter.chunk.size")

    @property
    def chunk_overlap(self) -> int:
        return settings.get_int("askai.text.splitter.chunk.overlap")

    @property
    def language(self) -> Language:
        # Lookup order: Settings -> Locale -> Environment
        return Language.of_locale(
            settings.get("askai.preferred.language")
            or locale.getlocale(locale.LC_ALL)
            or os.getenv("LC_ALL", os.getenv("LC_TYPE", os.getenv("LANG")))
            or Language.EN_US.idiom
        )

    @property
    def encoding(self) -> Charset:
        return self.language.encoding

    @property
    def max_iteractions(self) -> int:
        return settings.get_int("askai.max.router.iteractions")

    @property
    def max_short_memory_size(self) -> int:
        return settings.get_int("askai.max.short.memory.size")

    @property
    def max_router_retries(self) -> int:
        return settings.get_int("askai.max.agent.retries")

    @property
    def max_agent_execution_time_seconds(self) -> int:
        return settings.get_int("askai.max.agent.execution.time.seconds")

    @property
    def face_detect_alg(self) -> str:
        return settings.get("askai.camera.face-detect.alg")

    @property
    def scale_factor(self) -> float:
        return settings.get_float("askai.camera.scale.factor")

    @property
    def min_neighbors(self) -> int:
        return settings.get_int("askai.camera.min.neighbors")

    @property
    def min_max_size(self) -> tuple[int, ...]:
        return tuple(map(int, settings.get_list("askai.camera.min-max.size")))

    @property
    def max_id_distance(self) -> float:
        return settings.get_float("askai.camera.identity.max.distance")

    @property
    def recorder_phrase_limit_millis(self) -> int:
        return settings.get_int("askai.recorder.phrase.limit.millis")

    @property
    def recorder_silence_timeout_millis(self) -> int:
        return settings.get_int("askai.recorder.silence.timeout.millis")

    @property
    def recorder_noise_detection_duration_millis(self) -> int:
        return settings.get_int("askai.recorder.noise.detection.duration.millis")

    @property
    def recorder_input_device_auto_swap(self) -> bool:
        return settings.get_bool("askai.recorder.input.device.auto.swap")

    @property
    def recorder_devices(self) -> set[str]:
        return self._recorder_devices

    def add_device(self, device_name: str) -> None:
        """Add a new device to the configuration list."""
        if device_name not in self._recorder_devices:
            self._recorder_devices.add(device_name)
            settings.put("askai.recorder.devices", ", ".join(self._recorder_devices))

    def remove_device(self, device_name: str) -> None:
        """Remove a new device from the configuration list."""
        if device_name in self._recorder_devices:
            self._recorder_devices.remove(device_name)
            settings.put("askai.recorder.devices", ", ".join(self._recorder_devices))

assert (configs := AskAiConfigs().INSTANCE) is not None
