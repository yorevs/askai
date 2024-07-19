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
from collections import namedtuple
from pathlib import Path
from typing import Optional, Tuple

from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.modules.cache.ttl_cache import TTLCache

from askai.core.askai_configs import configs
from askai.core.askai_settings import ASKAI_DIR
from askai.core.support.utilities import hash_text

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

# Camera captures cache directory.
PICTURE_DIR: Path = Path(str(CACHE_DIR) + "/pictures")
if not PICTURE_DIR.exists():
    PICTURE_DIR.mkdir(parents=True, exist_ok=True)

# Voice recordings cache directory.
REC_DIR: Path = Path(str(CACHE_DIR) + "/recordings")
if not REC_DIR.exists():
    REC_DIR.mkdir(parents=True, exist_ok=True)

# Transcribed audio cache directory.
PERSIST_DIR: Path = Path(str(CACHE_DIR) + "/chroma")
if not PERSIST_DIR.exists():
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)

# RAG Directory
RAG_DIR: Path = Path(str(CACHE_DIR) + "/rag")
if not RAG_DIR.exists():
    RAG_DIR.mkdir(parents=True, exist_ok=True)


CacheEntry = namedtuple('CacheEntry', ["key", "expires"])


class CacheService(metaclass=Singleton):
    """Provide a cache service for previously used queries, audio generation, etc..."""

    INSTANCE: "CacheService"

    ASKAI_CACHE_KEYS = "askai-cache-keys"

    ASKAI_INPUT_CACHE_KEY = "askai-input-history"

    _TTL_CACHE: TTLCache[str] = TTLCache(ttl_minutes=configs.ttl)

    @staticmethod
    def get_audio_file(text: str, voice: str = "onyx", audio_format: str = "mp3") -> Tuple[str, bool]:
        """Retrieve the audio file path and whether it exists or not.
        :param text: Text to be cached. This is the text that the audio is speaking.
        :param voice: The voice used.
        :param audio_format: The audio format used.
        """
        key = f"{text.strip().lower()}-{hash_text(voice)}"
        audio_file_path = f"{str(AUDIO_DIR)}/askai-{hash_text(key)}.{audio_format}"
        return audio_file_path, file_is_not_empty(audio_file_path)

    def __init__(self):
        keys: str | None = self._TTL_CACHE.read(self.ASKAI_CACHE_KEYS)
        self._cache_keys: set[str] = set(map(str.strip, keys.split(',') if keys else {}))

    @property
    def keys(self) -> set[str]:
        return self._cache_keys

    def read_reply(self, text: str) -> Optional[str]:
        """Read AI replies from TTL cache.
        :param text: Text to be cached.
        """
        if configs.is_cache:
            key = text.strip().lower()
            return self._TTL_CACHE.read(key)
        return None

    def del_reply(self, text: str) -> Optional[str]:
        """Delete AI replies from TTL cache.
        :param text: Text to be deleted.
        """
        if configs.is_cache:
            key = text.strip().lower()
            self._TTL_CACHE.delete(key)
            self.keys.remove(key)
            self._TTL_CACHE.save(self.ASKAI_CACHE_KEYS, ','.join(self._cache_keys))
            return text
        return None

    def save_reply(self, text: str, reply: str) -> Optional[str]:
        """Save a AI reply into the TTL cache.
        :param text: Text to be cached.
        :param reply: The reply associated to this text.
        """
        if configs.is_cache:
            key = text.strip().lower()
            self._TTL_CACHE.save(key, reply)
            self.keys.add(key)
            self._TTL_CACHE.save(self.ASKAI_CACHE_KEYS, ','.join(self._cache_keys))
            return text
        return None

    def clear_replies(self) -> list[str]:
        """Clear all cached replies."""
        return list(map(self.del_reply, sorted(self.keys)))

    def read_query_history(self) -> list[str]:
        """Read the input queries from TTL cache."""
        hist_str: str = self._TTL_CACHE.read(self.ASKAI_INPUT_CACHE_KEY)
        return hist_str.split(",") if hist_str else []

    def save_query_history(self, history: list[str] = None) -> None:
        """Save the line input queries into the TTL cache."""
        self._TTL_CACHE.save(self.ASKAI_INPUT_CACHE_KEY, ",".join(history or KeyboardInput.history()))

    def load_history(self, predefined: list[str] = None) -> list[str]:
        """Load the suggester with user input history."""
        history = self.read_query_history()
        if predefined:
            history.extend(list(filter(lambda c: c not in history, predefined)))
        return history


assert (cache := CacheService().INSTANCE) is not None
