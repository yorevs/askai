#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.utils
      @file: utilities.py
   @created: Wed, 10 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import hashlib
from functools import lru_cache

from hspylib.core.enums.charset import Charset
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.core.tools.text_tools import ensure_endswith

from askai.__classpath__ import _Classpath

# AI Prompts directory.
PROMPT_DIR = str(_Classpath.resource_path()) + "/assets/prompts"


def hash_text(text: str) -> str:
    """Create a hash string based on the provided text.
    :param: text the text to be hashed.
    """
    return hashlib.md5(text.encode(Charset.UTF_8.val)).hexdigest()


@lru_cache
def calculate_delay_ms(audio_length_sec: float, text_length: int) -> float:
    """Calculate the required delay for one char to be printed according to the audio length in millis."""
    # Convert audio length from seconds to milliseconds
    audio_length_ms: float = audio_length_sec * 1000

    # Calculate characters per millisecond
    characters_per_ms: float = text_length * 1000 / audio_length_ms

    # Calculate delay in seconds for one character
    delay_sec = 1.0 / characters_per_ms

    return delay_sec * 1000


@lru_cache
def read_prompt(filename: str) -> str:
    """Read the prompt specified by the filename.
    :param filename: The filename of the prompt.
    """
    filename = f"{PROMPT_DIR}/{ensure_endswith(filename, '.txt')}"
    check_argument(file_is_not_empty(filename), f"Prompt file does not exist: {filename}")
    with open(filename) as f_prompt:
        return "".join(f_prompt.readlines())
