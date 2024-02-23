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
import os
from functools import lru_cache
from typing import Any

import pause
from clitt.core.term.cursor import Cursor
from hspylib.core.enums.charset import Charset
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import file_is_not_empty, sysout
from hspylib.core.tools.text_tools import ensure_endswith
from hspylib.modules.cli.vt100.vt_color import VtColor

from askai.__classpath__ import _Classpath
from askai.language.language import Language
from askai.utils.presets import Presets

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


def display_text(text: Any, end: str = os.linesep, erase_last=False) -> None:
    """TODO"""
    if erase_last:
        Cursor.INSTANCE.erase_line()
    sysout(text, end=end)


def stream_text(
    text: str,
    tempo: int = 1,
    language: Language = Language.EN_US
) -> None:
    """Stream the text on the screen. Simulates a typewriter effect. The following presets were
    benchmarked according to the selected language.
    :param text: the text to stream.
    :param tempo: the speed multiplier of the typewriter effect. Defaults to 1.
    :param language: the language used to stream the text. Defaults to en_US.
    """
    text: str = VtColor.strip_colors(text)
    presets: Presets = Presets.get(language.language, tempo=tempo)
    word_count: int = 0
    ln: str = os.linesep

    # The following algorithm was created based on the whisper voice.
    for i, char in enumerate(text):
        sysout(char, end="")
        if char.isalpha():
            pause.seconds(presets.base_speed)
        elif char.isnumeric():
            pause.seconds(
                presets.breath_interval
                if i + 1 < len(text) and text[i + 1] == "."
                else presets.number_interval
            )
        elif char.isspace():
            if i - 1 >= 0 and not text[i - 1].isspace():
                word_count += 1
                pause.seconds(
                    presets.breath_interval
                    if word_count % presets.words_per_breath == 0
                    else presets.words_interval
                )
            elif i - 1 >= 0 and not text[i - 1] in [".", "?", "!"]:
                word_count += 1
                pause.seconds(
                    presets.period_interval
                    if word_count % presets.words_per_breath == 0
                    else presets.punct_interval
                )
        elif char == "/":
            pause.seconds(
                presets.base_speed
                if i + 1 < len(text) and text[i + 1].isnumeric()
                else presets.punct_interval
            )
        elif char == ln:
            pause.seconds(
                presets.period_interval
                if i + 1 < len(text) and text[i + 1] == ln
                else presets.punct_interval
            )
            word_count = 0
        elif char in [":", "-"]:
            pause.seconds(
                presets.enum_interval
                if i + 1 < len(text) and (text[i + 1].isnumeric() or text[i + 1] in [" ", ln, "-"])
                else presets.base_speed
            )
        elif char in [",", ";"]:
            pause.seconds(
                presets.comma_interval if i + 1 < len(text) and text[i + 1].isspace() else presets.base_speed
            )
        elif char in [".", "?", "!", ln]:
            pause.seconds(presets.punct_interval)
            word_count = 0
        pause.seconds(presets.base_speed)
    sysout("")
