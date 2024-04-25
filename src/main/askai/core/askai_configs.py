#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.askai_configs
      @file: askai_configs.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.__classpath__ import classpath
from askai.core.askai_settings import settings
from askai.language.language import Language
from hspylib.core.enums.charset import Charset
from hspylib.core.metaclass.singleton import Singleton
from shutil import which

import os


class AskAiConfigs(metaclass=Singleton):
    """Provides access to AskAI configurations."""

    INSTANCE: "AskAiConfigs"

    # The resources folder
    RESOURCE_DIR = str(classpath.resource_path())

    def __init__(self):
        self._language: Language = Language.of_locale(
            os.getenv("LC_ALL", os.getenv("LC_TYPE", os.getenv("LANG", os.getenv("LANGUAGE", "en_US.UTF-8"))))
        )
        self._recorder_devices: list[str] = settings.get_list("askai.recorder.devices")

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
        settings.put("askai.speak.enabled", which("ffplay") and value)

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
        return settings.get_int("askai.speech.tempo")

    @tempo.setter
    def tempo(self, value: int) -> None:
        settings.get_int("askai.speech.tempo", value)

    @property
    def language(self) -> Language:
        return self._language

    @property
    def encoding(self) -> Charset:
        return self.language.encoding

    @property
    def ttl(self) -> int:
        return settings.get_int("askai.cache.ttl.minutes")

    @property
    def max_iteractions(self) -> int:
        return settings.get_int("askai.max.iteractions")

    @property
    def max_context_size(self) -> int:
        return settings.get_int("askai.max.context.size")

    @property
    def max_router_retries(self) -> int:
        return settings.get_int("askai.max.router.retries")

    @property
    def max_agent_execution_time_seconds(self) -> int:
        return settings.get_int("askai.max.agent.execution.time.seconds")

    @property
    def recorder_devices(self) -> list[str]:
        return self._recorder_devices

    def add_device(self, device_name: str) -> None:
        self._recorder_devices.append(device_name)
        settings.put("askai.recorder.devices", ", ".join(self._recorder_devices))

    def remove_device(self, device_name: str) -> None:
        self._recorder_devices.remove(device_name)
        settings.put("askai.recorder.devices", ", ".join(self._recorder_devices))


assert (configs := AskAiConfigs().INSTANCE) is not None
