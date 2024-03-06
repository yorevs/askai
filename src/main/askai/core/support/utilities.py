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
from os.path import dirname
from pathlib import Path
from typing import Any, Optional, Tuple

import pause
from clitt.core.term.cursor import Cursor
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import sysout

from askai.core.support.presets import Presets
from askai.language.language import Language


def hash_text(text: str) -> str:
    """Create a hash string based on the provided text.
    :param: text the text to be hashed.
    """
    return hashlib.md5(text.encode(Charset.UTF_8.val)).hexdigest()


def extract_path(command_line: str, flags: int = re.IGNORECASE | re.MULTILINE) -> Optional[str]:
    """TODO"""
    # Match a file or folder path within a command line.
    re_path = r'(?:\w)\s(?:-[\w\d]+\s)*(?:([\/\w\d\s"\\.-]+)|(".*?"))'
    if command_line and (cmd_path := re.search(re_path, command_line, flags)):
        if (
            (extracted := cmd_path.group(1).strip().replace('\\ ', ' ')) and
            (_path_ := Path(extracted)).exists()
        ):
            if _path_.is_dir() or (extracted := dirname(extracted)):
                return extracted if extracted and Path(extracted).is_dir() else None
    return None


def extract_command(response_text: str, flags: int = re.IGNORECASE | re.MULTILINE) -> Optional[Tuple[str, str]]:
    """TODO"""
    # Match a terminal command formatted in a markdown code block.
    re_command = r'^`{3}((\w+)\s*)?(.+)\s*?`{3}$'
    if response_text and (mat := re.search(re_command, response_text.replace('\n', ' ').strip(), flags)):
        if mat and len(mat.groups()) == 3:
            shell, cmd = mat.group(1) or '', mat.group(3) or ''
            return shell.strip(), cmd.strip()

    return None


def beautify(text: Any) -> str:
    # fmt: off
    text = str(text)
    text = re.sub("Hints?( and [Tt]ips)?:[ \n]*", "  Tips: ", text, re.IGNORECASE)
    text = re.sub("Analysis:[ \n]*", "  Analysis: ", text, re.IGNORECASE)
    text = re.sub("Summary:[ \n]*", "  Summary:", text, re.IGNORECASE)
    text = re.sub("(Joke( [Tt]ime)?):[ \n]*", "  Joke: ", text, re.IGNORECASE)
    text = re.sub("Fun [Ff]acts?:[ \n]*", "  Fun Fact: ", text, re.IGNORECASE)
    text = re.sub("Advice:[ \n]*", "  Advice: ", text, re.IGNORECASE)
    # fmt: on

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
    text: str = beautify(text)
    presets: Presets = Presets.get(language.language, tempo=tempo)
    word_count: int = 0
    ln: str = os.linesep

    # The following algorithm was created based on the whisper voice.
    sysout("%GREEN%", end="")
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
    sysout("%NC%")
