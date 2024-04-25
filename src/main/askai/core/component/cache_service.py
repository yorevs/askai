#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.component
      @file: cache_service.py
   @created: Tue, 16 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_settings import ASKAI_DIR
from askai.core.support.utilities import hash_text
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.modules.cache.ttl_cache import TTLCache
from pathlib import Path
from typing import Optional, Tuple

# AskAI cache root directory.
CACHE_DIR: Path = Path(f"{ASKAI_DIR}/cache")

# Settings directory.
SETTINGS_DIR: Path = Path(str(ASKAI_DIR) + "/settings")
if not SETTINGS_DIR.exists():
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

# Transcribed audio cache directory.
AUDIO_DIR: Path = Path(str(CACHE_DIR) + "/audio")
if not AUDIO_DIR.exists():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Voice recordings cache directory.
REC_DIR: Path = Path(str(CACHE_DIR) + "/recordings")
if not REC_DIR.exists():
    REC_DIR.mkdir(parents=True, exist_ok=True)

# Transcribed audio cache directory.
PERSIST_DIR: Path = Path(str(CACHE_DIR) + "/chroma")
if not PERSIST_DIR.exists():
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)


class CacheService(metaclass=Singleton):
    """Provide a cache service for previously used queries, audio generation, etc..."""

    INSTANCE: "CacheService"

    ASKAI_INPUT_CACHE_KEY = "askai-input-history"

    DISABLE_CACHE = True

    _TTL_CACHE: TTLCache[str] = TTLCache(ttl_minutes=30)

    @classmethod
    def set_cache_enable(cls, enable: bool) -> bool:
        """Enable or disable caching. Is does not clear current cached entries, but it does not retrieve or save new
        ones while not re-enabled."""
        cls.DISABLE_CACHE = not enable
        return cls.DISABLE_CACHE

    @classmethod
    def is_cache_enabled(cls) -> bool:
        return not cls.DISABLE_CACHE

    @classmethod
    def read_reply(cls, text: str) -> Optional[str]:
        """Read AI replies from TTL cache.
        :param text: Text to be cached.
        """
        if cls.DISABLE_CACHE:
            return None
        key = text.strip().lower()
        return cls._TTL_CACHE.read(key)

    @classmethod
    def save_reply(cls, text: str, reply: str) -> None:
        """Save a AI reply into the TTL cache.
        :param text: Text to be cached.
        :param reply: The reply associated to this text.
        """
        if cls.DISABLE_CACHE:
            return
        key = text.strip().lower()
        cls._TTL_CACHE.save(key, reply)

    @classmethod
    def read_query_history(cls) -> None:
        """Read the input queries from TTL cache."""
        hist_str: str = cls._TTL_CACHE.read(cls.ASKAI_INPUT_CACHE_KEY)
        if hist_str:
            KeyboardInput.preload_history(hist_str.split(","))

    @classmethod
    def save_query_history(cls) -> None:
        """Save the line input queries into the TTL cache."""
        hist = KeyboardInput.history()
        cls._TTL_CACHE.save(cls.ASKAI_INPUT_CACHE_KEY, ",".join(hist))

    @classmethod
    def get_audio_file(cls, text: str, audio_format: str = "mp3") -> Tuple[str, bool]:
        """Retrieve the audio file path and whether it exists or not.
        :param text: Text to be cached. This is the text that the audio is speaking.
        :param audio_format: The audio format used.
        """
        key = text.strip().lower()
        audio_file_path = f"{str(AUDIO_DIR)}/askai-{hash_text(key)}.{audio_format}"
        return audio_file_path, file_is_not_empty(audio_file_path)


assert (cache := CacheService().INSTANCE) is not None
