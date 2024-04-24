#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.askai_configs
      @file: askai_configs.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import os
from shutil import which

from hspylib.core.config.app_config import AppConfigs
from hspylib.core.enums.charset import Charset
from hspylib.core.metaclass.singleton import Singleton

from askai.__classpath__ import classpath
from askai.language.language import Language


class AskAiConfigs(metaclass=Singleton):
    """Provides access to AskAI configurations."""

    INSTANCE: "AskAiConfigs"

    # The resources folder
    RESOURCE_DIR = str(classpath.resource_path())

    def __init__(self):
        self._configs = AppConfigs.INSTANCE or AppConfigs(self.RESOURCE_DIR)
        self._is_interactive: bool = self._configs.get_bool("askai.interactive.enabled")
        self._is_speak: bool = self._configs.get_bool("askai.speak.enabled")
        self._is_debug: bool = self._configs.get_bool("askai.debug.enabled")
        self._is_cache: bool = self._configs.get_bool("askai.cache.enabled")
        self._tempo: int = self._configs.get_int("askai.speech.tempo")
        self._language: Language = Language.of_locale(
            os.getenv("LC_ALL", os.getenv("LC_TYPE", os.getenv("LANG", os.getenv("LANGUAGE", "en_US.UTF-8"))))
        )
        self._ttl: int = self._configs.get_int("askai.cache.ttl.minutes")
        self._max_context_size: int = self._configs.get_int("askai.max.context.size")
        self._max_iteractions: int = self._configs.get_int("askai.max.iteractions")
        self._max_router_retries: int = self._configs.get_int("askai.max.router.retries")

    @property
    def is_interactive(self) -> bool:
        return self._is_interactive

    @is_interactive.setter
    def is_interactive(self, value: bool) -> None:
        self._is_interactive = value

    @property
    def is_speak(self) -> bool:
        return which("ffplay") and self._is_speak

    @is_speak.setter
    def is_speak(self, value: bool) -> None:
        self._is_speak = which("ffplay") and value

    @property
    def is_debug(self) -> bool:
        return self._is_debug

    @is_debug.setter
    def is_debug(self, value: bool) -> None:
        self._is_debug = value

    @property
    def is_cache(self) -> bool:
        return self._is_cache

    @is_cache.setter
    def is_cache(self, value: bool) -> None:
        self._is_cache = value

    @property
    def tempo(self) -> int:
        return self._tempo

    @tempo.setter
    def tempo(self, value: int) -> None:
        self._tempo = value

    @property
    def language(self) -> Language:
        return self._language

    @property
    def encoding(self) -> Charset:
        return self.language.encoding

    @property
    def ttl(self) -> int:
        return self._ttl

    @property
    def max_iteractions(self) -> int:
        return self._max_iteractions

    @property
    def max_context_size(self) -> int:
        return self._max_context_size

    @property
    def max_router_retries(self) -> int:
        return self._max_router_retries


assert (configs := AskAiConfigs().INSTANCE) is not None
