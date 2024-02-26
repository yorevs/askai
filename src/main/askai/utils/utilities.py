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
from typing import Any

import pause
from clitt.core.term.cursor import Cursor
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import sysout
from hspylib.modules.cli.vt100.vt_color import VtColor

from askai.language.language import Language
from askai.utils.presets import Presets


def hash_text(text: str) -> str:
    """Create a hash string based on the provided text.
    :param: text the text to be hashed.
    """
    return hashlib.md5(text.encode(Charset.UTF_8.val)).hexdigest()


def display_text(text: Any, end: str = os.linesep, erase_last=False) -> None:
    """TODO"""
    if erase_last:
        Cursor.INSTANCE.erase_line()
    sysout(f"%EL0%{text}", end=end)


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
