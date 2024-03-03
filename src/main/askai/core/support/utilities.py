#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.support
      @file: utilities.py
   @created: Wed, 10 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import hashlib
import os
import re
from typing import Any, List

import pause
from clitt.core.term.cursor import Cursor
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import sysout
from hspylib.modules.cli.vt100.vt_color import VtColor

from askai.core.support.presets import Presets
from askai.language.language import Language


def hash_text(text: str) -> str:
    """Create a hash string based on the provided text.
    :param: text the text to be hashed.
    """
    return hashlib.md5(text.encode(Charset.UTF_8.val)).hexdigest()


def beautify(text: Any) -> str:
    codes: List[str] = [
        '&br;', '&nbsp;', '&error;', '&lamp;', '&poop;', '&smile;', '&star;'
    ]
    icons: List[str] = [
        '\n', ' ', '', '', '', '', ''
    ]
    text: str = str(text)
    for code, icon in zip(codes, icons):
        text = text.replace(code, icon)
    text: str = text.replace('\n', '␊')
    text: str = re.sub(r'␊{3,}', '␊␊', text)
    text: str = re.sub(r'[^:]␊␊([0-9]\. |[-*] )', r'␊\1', text)
    text: str = re.sub(r':␊([0-9]\. |[-*] )', r':␊␊\1', text)
    text: str = text.replace('␊', '\n')
    return text


def display_text(text: Any, end: str = os.linesep, erase_last=False) -> None:
    """Display the provided text ina proper way.
    :param text: The text to be displayed.
    :param end: String appended after the last value, default a newline.
    :param erase_last: Whether to erase the last displayed line.
    """
    if erase_last:
        Cursor.INSTANCE.erase_line()
    text: str = beautify(text)
    sysout(f"%EL0%{text}", end=end)


def stream_text(
    text: Any,
    tempo: int = 1,
    language: Language = Language.EN_US
) -> None:
    """Stream the text on the screen. Simulates a typewriter effect. The following presets were
    benchmarked according to the selected language.
    :param text: the text to stream.
    :param tempo: the speed multiplier of the typewriter effect. Defaults to 1.
    :param language: the language used to stream the text. Defaults to en_US.
    """
    text: str = beautify(VtColor.strip_colors(text))
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


if __name__ == '__main__':
    s = """
  ChatGPT: Here is a summarized version of the command output:

- File: Finance alias, Size: 920B, Modified: Sep 1 2022

- Folder: Apps, Size: 480B, Modified: Nov 5 2021

- Folder: Fotos-Aniversario-Gabriel, Size: 9.8K, Modified: Sep 17 2022

- Folder: Fotos-Consagracao-Gabriel, Size: 1.2K, Modified: Nov 8 2021

- Folder: Images, Size: 512B, Modified: Jun 8 2022


Summary: Total items: 5, Omitted items: 2

 Hint: 'There are 2 more items in this directory. Try using the "ls -lh" command to see the full list.'

"""
    display_text(s)
