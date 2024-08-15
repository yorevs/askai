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
from askai.__classpath__ import classpath
from askai.core.support.text_formatter import text_formatter
from contextlib import redirect_stdout
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import to_bool
from io import StringIO
from pathlib import Path
from rich.table import Table
from setman.settings.settings import Settings
from setman.settings.settings_config import SettingsConfig
from setman.settings.settings_entry import SettingsEntry
from typing import Any, Optional

import logging as log
import os
import re

# AskAI config directory.
ASKAI_DIR: Path = Path(f'{os.getenv("ASKAI_DIR", os.getenv("HHS_DIR", str(Path.home())))}/askai')
if not ASKAI_DIR.exists():
    ASKAI_DIR.mkdir(parents=True, exist_ok=True)

# Make sure the AskAI directory is exported.
os.environ["ASKAI_DIR"] = str(ASKAI_DIR)


class AskAiSettings(metaclass=Singleton):
    """The Setman Settings."""

    INSTANCE: "AskAiSettings"

    RESOURCE_DIR = str(classpath.resource_path())

    _ACTUAL_VERSION: str = "0.1.8"

    def __init__(self) -> None:
        self._configs = SettingsConfig(self.RESOURCE_DIR, "application.properties")
        self._settings = Settings(self._configs)
        if not self._settings.count() or self.get("askai.settings.version.id") != self._ACTUAL_VERSION:
            self.defaults()

    def __str__(self) -> str:
        return self.search()

    def __repr__(self) -> str:
        return self.__str__()

    def __getitem__(self, name: str) -> Optional[SettingsEntry]:
        return self._settings.get(name)

    def __setitem__(self, name: str, item: Any) -> None:
        self._settings.put(name, name[: name.find(".")], item)

    @property
    def settings(self) -> Settings:
        return self._settings

    def search(self, filters: str | None = None) -> Optional[str]:
        """Search setting using the specified filters.
        :param filters: Filters used on the search.
        """
        data = [(s.name, s.value) for s in self._settings.search(filters)]
        if data:
            table = Table(title="AskAI - Settings")
            table.add_column("No.", style="white", no_wrap=True)
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Value", style="green", no_wrap=True)
            for i, d in enumerate(data):
                table.add_row(str(i), d[0], d[1])
            with StringIO() as buf, redirect_stdout(buf):
                text_formatter.console.print(table)
                return buf.getvalue()
        return None

    def defaults(self) -> None:
        """Create the default settings database if they doesn't exist."""
        # AskAI General
        self._settings.clear()
        self._settings.put("askai.settings.version.id", "askai", self._ACTUAL_VERSION)
        self._settings.put("askai.debug.enabled", "askai", False)
        self._settings.put("askai.speak.enabled", "askai", False)
        self._settings.put("askai.cache.enabled", "askai", False)
        self._settings.put("askai.cache.ttl.minutes", "askai", 25)
        self._settings.put("askai.text.to.speech.tempo", "askai", 1)
        self._settings.put("askai.text.splitter.chunk.size", "askai", 1000)
        self._settings.put("askai.text.splitter.chunk.overlap", "askai", 100)
        self._settings.put("askai.preferred.language", "askai", '')
        self._settings.put("askai.default.engine", "askai", "openai")
        self._settings.put("askai.default.engine.model", "askai", "gpt-4o-mini")
        # Router
        self._settings.put("askai.max.short.memory.size", "askai", 10)
        self._settings.put("askai.max.router.iteractions", "askai", 30)
        self._settings.put("askai.max.agent.retries", "askai", 3)
        self._settings.put("askai.max.agent.execution.time.seconds", "askai", 45)
        # Recorder
        self._settings.put("askai.recorder.devices", "askai", "")
        self._settings.put("askai.recorder.silence.timeout.millis", "askai", 1200)
        self._settings.put("askai.recorder.phrase.limit.millis", "askai", 10000)
        self._settings.put("askai.recorder.noise.detection.duration.millis", "askai", 600)
        self._settings.put("askai.recorder.input.device.auto.swap", "askai", True)
        # Camera
        self._settings.put("askai.camera.face-detect.alg", "askai", "haarcascade_frontalface_default.xml")
        self._settings.put("askai.camera.scale.factor", "askai", 1.1)
        self._settings.put("askai.camera.min.neighbors", "askai", 3)
        self._settings.put("askai.camera.min-max.size", "askai", "60, 60")
        self._settings.put("askai.camera.identity.max.distance", "askai", 0.70)
        # OpenAI
        self._settings.put("openai.speech.to.text.model", "openai", "whisper-1")
        self._settings.put("openai.text.to.speech.model", "openai", "tts-1")
        self._settings.put("openai.text.to.speech.voice", "openai", "onyx")
        self._settings.put("openai.text.to.speech.audio.format", "openai", "mp3")
        log.debug(f"Settings database created !")

    def get(self, key: str, default_value: str | None = "") -> str:
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
        str_val: str = self.get(key) or ""
        val: list | None = None
        if str_val:
            val: list = re.split(r"[;,|]", str_val)
        return val or default_value or []


assert (settings := AskAiSettings().INSTANCE) is not None
