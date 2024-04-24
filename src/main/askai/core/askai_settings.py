#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.support
      @file: askai_settings.py
   @created: Tue, 23 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import logging as log
import os
import re
from pathlib import Path
from typing import Any, Optional

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import to_bool
from setman.settings.settings import Settings
from setman.settings.settings_config import SettingsConfig
from setman.settings.settings_entry import SettingsEntry

from askai.__classpath__ import classpath


# AskAI config directory.
ASKAI_DIR: Path = Path(f'{os.getenv("HHS_DIR", os.getenv("ASKAI_DIR", os.getenv("TEMP", "/tmp")))}/askai')
if not ASKAI_DIR.exists():
    ASKAI_DIR: Path = classpath.resource_path()

# Make sure the AskAI directory is exported.
os.environ["ASKAI_DIR"] = str(ASKAI_DIR)


class AskAiSettings(metaclass=Singleton):
    """The Setman Settings."""

    INSTANCE: 'AskAiSettings'

    RESOURCE_DIR = str(classpath.resource_path())

    _ACTUAL_VERSION: str = '0.0.3'

    def __init__(self) -> None:
        self._configs = SettingsConfig(self.RESOURCE_DIR, "application.properties")
        self._settings = Settings(self._configs)
        if not self._settings.count() or self.get("askai.settings.version.id") != self._ACTUAL_VERSION:
            self._defaults()

    def __str__(self) -> str:
        return str(self._settings)

    def __repr__(self) -> str:
        return self.__str__()

    def __getitem__(self, name: str) -> Optional[SettingsEntry]:
        return self._settings.get(name)

    def __setitem__(self, name: str, item: Any) -> None:
        self._settings.put(name, name[:name.find('.')], item)

    def _defaults(self) -> None:
        """Create the default settings database if they doesn't exist."""
        # AskAI General
        self._settings.clear()
        self._settings.put("askai.settings.version.id", "askai", self._ACTUAL_VERSION)
        self._settings.put("askai.debug.enabled", "askai", False)
        self._settings.put("askai.speak.enabled", "askai", False)
        self._settings.put("askai.cache.enabled", "askai", False)
        self._settings.put("askai.cache.ttl.minutes", "askai", 30)
        self._settings.put("askai.speech.tempo", "askai", 1)
        # Router
        self._settings.put("askai.max.context.size", "askai", 3)
        self._settings.put("askai.max.iteractions", "askai", 30)
        self._settings.put("askai.max.router.retries", "askai", 3)
        self._settings.put("askai.max.agent.execution.time.seconds", "askai", 120)
        # Recorder
        self._settings.put("askai.recorder.devices", "askai", "")
        self._settings.put("askai.recorder.silence.timeout.millis", "askai", 1500)
        self._settings.put("askai.recorder.phrase.limit.millis", "askai", 0)
        # OpenAI
        self._settings.put("openai.speech.to.text.model", "openai", "whisper-1")
        self._settings.put("openai.text.to.speech.model", "openai", "tts-1")
        self._settings.put("openai.text.to.speech.voice", "openai", "onyx")
        self._settings.put("openai.text.to.speech.audio.format", "openai", "mp3")
        log.debug(f"Settings database created !")

    def get(self, key: str, default_value: str | None = '') -> str:
        val = self.__getitem__(key)
        return str(val.value) if val else default_value

    def put(self, key: str, value: Any) -> None:
        self.__setitem__(key, value)

    def get_bool(self, key: str, default_value: bool | None = False) -> bool:
        return to_bool(self.get(key) or default_value)

    def get_int(self, key: str, default_value: int | None = 0) -> int:
        try:
            return int(self.get(key) or default_value)
        except ValueError:
            return 0

    def get_float(self, key: str, default_value: float | None = 0.0) -> float:
        try:
            return float(self.get(key) or default_value)
        except ValueError:
            return 0

    def get_list(self, key: str, default_value: list | None = None) -> list:
        str_val: str = self.get(key) or ''
        val: list | None = None
        if str_val:
            val: list = re.split(r'[;,|]', str_val)
        return val or default_value or []


assert (settings := AskAiSettings().INSTANCE) is not None
