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
import mimetypes
import os
import re
import sys
from os.path import basename, dirname
from pathlib import Path
from typing import Any, Optional, Tuple

import pause
from clitt.core.term.cursor import Cursor
from hspylib.core.enums.charset import Charset
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import file_is_not_empty, sysout
from hspylib.core.tools.text_tools import ensure_endswith
from hspylib.modules.cli.vt100.vt_color import VtColor

from askai.core.support.presets import Presets
from askai.core.support.text_formatter import text_formatter
from askai.language.language import Language


def read_stdin() -> Optional[str]:
    """TODO"""
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def display_text(text: Any, prefix: Any = "", markdown: bool = True, erase_last=False) -> None:
    """Display the provided text ina proper way.
    :param text: The text to be displayed.
    :param prefix: the text prefix.
    :param markdown: Whether to enable markdown rendering.
    :param erase_last: Whether to erase the last displayed line.
    """
    if erase_last:
        Cursor.INSTANCE.erase_line()
    if markdown:
        text_formatter.display_markdown(f"{str(prefix)}{text}")
    else:
        text_formatter.display_text(f"{str(prefix)}{text}")


def stream_text(text: Any, prefix: Any = "", tempo: int = 1, language: Language = Language.EN_US) -> None:
    """Stream the text on the screen. Simulates a typewriter effect. The following presets were
    benchmarked according to the selected language.
    :param text: the text to stream.
    :param prefix: the streaming prefix.
    :param tempo: the speed multiplier of the typewriter effect. Defaults to 1.
    :param language: the language used to stream the text. Defaults to en_US.
    """
    text: str = text_formatter.beautify(text)
    presets: Presets = Presets.get(language.language, tempo=tempo)
    word_count: int = 0
    ln: str = os.linesep
    hide: bool = False
    idx: int = 0

    # The following algorithm was created based on the whisper voice.
    sysout(f"{str(prefix)}", end="")
    for i, char in enumerate(text):
        if char == "%" and (i + 1) < len(text):
            try:
                if (color := text[i + 1 : text.index("%", i + 1)]) in VtColor.names():
                    hide, idx = True, text.index("%", i + 1)
                    sysout(f"%{color}%", end="")
                    continue
            except ValueError:
                pass  # this means that this '%' is not a VtColor specification
        if hide and idx is not None and i <= idx:
            continue
        sysout(char, end="")
        if char.isalpha():
            pause.seconds(presets.base_speed)
        elif char.isnumeric():
            pause.seconds(
                presets.breath_interval if i + 1 < len(text) and text[i + 1] == "." else presets.number_interval
            )
        elif char.isspace():
            if i - 1 >= 0 and not text[i - 1].isspace():
                word_count += 1
                pause.seconds(
                    presets.breath_interval if word_count % presets.words_per_breath == 0 else presets.words_interval
                )
            elif i - 1 >= 0 and not text[i - 1] in [".", "?", "!"]:
                word_count += 1
                pause.seconds(
                    presets.period_interval if word_count % presets.words_per_breath == 0 else presets.punct_interval
                )
        elif char == "/":
            pause.seconds(
                presets.base_speed if i + 1 < len(text) and text[i + 1].isnumeric() else presets.punct_interval
            )
        elif char == ln:
            pause.seconds(
                presets.period_interval if i + 1 < len(text) and text[i + 1] == ln else presets.punct_interval
            )
            word_count = 0
        elif char in [":", "-"]:
            pause.seconds(
                presets.enum_interval
                if i + 1 < len(text) and (text[i + 1].isnumeric() or text[i + 1] in [" ", ln, "-"])
                else presets.base_speed
            )
        elif char in [",", ";"]:
            pause.seconds(presets.comma_interval if i + 1 < len(text) and text[i + 1].isspace() else presets.base_speed)
        elif char in [".", "?", "!", ln]:
            pause.seconds(presets.punct_interval)
            word_count = 0
        pause.seconds(presets.base_speed)
    sysout("%NC%")


def read_resource(base_dir: str, filename: str, file_ext: str = ".txt") -> str:
    """Read the prompt template specified by the filename.
    :param base_dir: The base directory, relative to the resources folder.
    :param filename: The filename of the prompt.
    :param file_ext: The file extension of.
    """
    filename = f"{base_dir}/{ensure_endswith(basename(filename), file_ext)}"
    check_argument(file_is_not_empty(filename), f"Resource file is empty does not exist: {filename}")
    return Path(filename).read_text(encoding=Charset.UTF_8.val)


def hash_text(text: str) -> str:
    """Create a hash string based on the provided text.
    :param: text the text to be hashed.
    """
    return hashlib.md5(text.encode(Charset.UTF_8.val)).hexdigest()


def extract_path(command_line: str, flags: int = re.IGNORECASE | re.MULTILINE) -> Optional[str]:
    """Extract the first identifiable path of the executed command line.
    :param command_line: The command line text.
    :param flags: Regex match flags.
    """
    command_line = re.sub("([12&]>|2>&1|1>&2).+", "", command_line.split("|")[0])
    re_path = r'(?:\w)\s+(?:-[\w\d]+\s)*(?:([\/\w\d\s"-]+)|(".*?"))'
    if command_line and (cmd_path := re.search(re_path, command_line, flags)):
        if (extracted := cmd_path.group(1).strip().replace("\\ ", " ")) and (_path_ := Path(extracted)).exists():
            if _path_.is_dir() or (extracted := dirname(extracted)):
                return extracted if extracted and Path(extracted).is_dir() else None
    return None


def extract_command(markdown_text: str, flags: int = re.IGNORECASE | re.MULTILINE) -> Optional[Tuple[str, str]]:
    """Extract command from the markdown code block formatted text.
    :param markdown_text: The markdown formatted command line text.
    :param flags: Regex match flags.
    """
    # Match a terminal command formatted in a markdown code block.
    re_command = r"^`{3}((\w+)\s*)?(.+)\s*?`{3}$"
    if markdown_text and (mat := re.search(re_command, markdown_text.replace("\n", " ").strip(), flags)):
        if mat and len(mat.groups()) == 3:
            shell, cmd = mat.group(1) or "", mat.group(3) or ""
            return shell.strip(), cmd.strip()
    return None


def media_type_of(pathname: str) -> Optional[tuple[str, ...]] | None:
    """Return the file media type, or none is guessing was not possible.
    :param pathname: The file path to check.
    """
    mimetypes.init()
    mtype, _ = mimetypes.guess_type(basename(pathname))

    if mtype is not None:
        return tuple(mtype.split('/'))

    return None
