#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.component
      @file: cache_service.py
   @created: Tue, 16 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_configs import configs
from askai.core.askai_settings import ASKAI_DIR
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from collections import namedtuple
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.core.tools.text_tools import hash_text
from hspylib.modules.cache.ttl_cache import TTLCache
from pathlib import Path
from typing import Optional

import re

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

# Camera photo shots cache directory.
PICTURE_DIR: Path = Path(str(CACHE_DIR) + "/pictures")
if not PICTURE_DIR.exists():
    PICTURE_DIR.mkdir(parents=True, exist_ok=True)

# Camera photo shots cache directory.
PHOTO_DIR: Path = Path(str(PICTURE_DIR) + "/photos")
if not PHOTO_DIR.exists():
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)

# Detected faces cache directory.
FACE_DIR: Path = Path(str(PICTURE_DIR) + "/faces")
if not FACE_DIR.exists():
    FACE_DIR.mkdir(parents=True, exist_ok=True)

# Imported image files cache directory.
IMG_IMPORTS_DIR: Path = Path(str(PICTURE_DIR) + "/imports")
if not IMG_IMPORTS_DIR.exists():
    IMG_IMPORTS_DIR.mkdir(parents=True, exist_ok=True)

# AI Generation cache directory.
GEN_AI_DIR: Path = Path(str(CACHE_DIR) + "/generated")
if not GEN_AI_DIR.exists():
    GEN_AI_DIR.mkdir(parents=True, exist_ok=True)

# Voice recordings cache directory.
REC_DIR: Path = Path(str(CACHE_DIR) + "/recordings")
if not REC_DIR.exists():
    REC_DIR.mkdir(parents=True, exist_ok=True)

# Transcribed audio cache directory.
PERSIST_DIR: Path = Path(str(CACHE_DIR) + "/chroma")
if not PERSIST_DIR.exists():
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)


CacheEntry = namedtuple("CacheEntry", ["key", "expires"])


class CacheService(metaclass=Singleton):
    """Provide a cache service for previously used queries, audio generation, and other recurring operations. This
    class is designed to store and retrieve cached data efficiently, reducing the need for repeated processing and
    enhancing performance.
    """

    INSTANCE: "CacheService"

    ASKAI_CACHE_KEYS: str = "askai-cache-keys"

    ASKAI_INPUT_CACHE_KEY: str = "askai-input-history"

    ASKAI_CONTEXT_KEY: str = "askai-context-key"

    _TTL_CACHE: TTLCache[str] = TTLCache(ttl_minutes=configs.ttl)

    def __init__(self):
        keys: str | None = self._TTL_CACHE.read(self.ASKAI_CACHE_KEYS)
        self._cache_keys: set[str] = set(map(str.strip, keys.split(",") if keys else {}))

    @property
    def keys(self) -> set[str]:
        return self._cache_keys

    def audio_file_path(self, text: str, voice: str = "onyx", audio_format: str = "mp3") -> tuple[str, bool]:
        """Retrieve the hashed audio file path and determine whether the file already exists.
        :param text: The text that the audio represents.
        :param voice: The AI voice used for speech synthesis (default is "onyx").
        :param audio_format: The audio file format (default is "mp3").
        :return: A tuple containing the hashed file path as a string and a boolean indicating if the file exists.
        """
        key = f"{text.strip().lower()}-{hash_text(voice)}"
        audio_file_path = f"{str(AUDIO_DIR)}/askai-{hash_text(key)}.{audio_format}"
        return audio_file_path, file_is_not_empty(audio_file_path)

    def save_reply(self, text: str, reply: str) -> Optional[str]:
        """Save an AI reply into the TTL (Time-To-Live) cache.
        :param text: The text to be cached.
        :param reply: The AI reply associated with this text.
        :return: The key under which the reply is saved, or None if the save operation fails.
        """
        if configs.is_cache:
            key = text.strip().lower()
            self._TTL_CACHE.save(key, reply)
            self.keys.add(key)
            self._TTL_CACHE.save(self.ASKAI_CACHE_KEYS, ",".join(self._cache_keys))
            return key
        return None

    def read_reply(self, text: str) -> Optional[str]:
        """Retrieve AI replies from the TTL (Time-To-Live) cache.
        :param text: The text key to look up in the cache.
        :return: The cached reply associated with the text, or None if not found.
        """
        if configs.is_cache:
            key = text.strip().lower()
            return self._TTL_CACHE.read(key)
        return None

    def del_reply(self, text: str) -> Optional[str]:
        """Delete an AI reply from the TTL (Time-To-Live) cache.
        :param text: The text key whose associated reply is to be deleted from the cache.
        :return: The deleted reply if it existed, or None if no reply was found.
        """
        if configs.is_cache:
            key = text.strip().lower()
            self._TTL_CACHE.delete(key)
            self.keys.remove(key)
            self._TTL_CACHE.save(self.ASKAI_CACHE_KEYS, ",".join(self._cache_keys))
            return text
        return None

    def clear_replies(self) -> list[str]:
        """Clear all cached replies.
        :return: A list of keys for the replies that were deleted from the cache.
        """
        return list(map(self.del_reply, sorted(self.keys)))

    def read_input_history(self) -> list[str]:
        """Retrieve line input queries from the TTL (Time-To-Live) cache.
        :return: A list of input queries stored in the cache.
        """
        hist_str: str = self._TTL_CACHE.read(self.ASKAI_INPUT_CACHE_KEY)
        return hist_str.split(",") if hist_str else []

    def save_input_history(self, history: list[str] = None) -> str:
        """Save input queries into the TTL (Time-To-Live) cache.
        :param history: A list of input queries to be saved. If None, the current input history will be saved.
        :return: The temporary file name of the saved entry.
        """
        return self._TTL_CACHE.save(self.ASKAI_INPUT_CACHE_KEY, ",".join(history or KeyboardInput.history()))

    def load_input_history(self, predefined: list[str] = None) -> list[str]:
        """Load input queries from the TTL (Time-To-Live) cache extending it with a predefined input history.
        :param predefined: A list of predefined input queries to be appended to the final list.
        :return: A list of input queries loaded from the cache.
        """
        history = self.read_input_history()
        if predefined:
            history.extend(list(filter(lambda c: c not in history, predefined)))
        return history

    def save_context(self, context: list[str]) -> None:
        """Save the context window entries into the TTL (Time-To-Live) cache.
        :param context: A list of context entries to be saved.
        """
        self._TTL_CACHE.save(self.ASKAI_CONTEXT_KEY, "%EOL%".join(context))

    def read_context(self) -> list[str]:
        """Read the context window entries from the TTL (Time-To-Live) cache.
        :return: A list of context entries retrieved from the cache."""
        ctx_str: str = self._TTL_CACHE.read(self.ASKAI_CONTEXT_KEY)
        return re.split(r"%EOL%", ctx_str, flags=re.MULTILINE | re.IGNORECASE) if ctx_str else []


assert (cache := CacheService().INSTANCE) is not None
