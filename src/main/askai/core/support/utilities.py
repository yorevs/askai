#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.support.utilities
      @file: utilities.py
   @created: Wed, 10 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import base64
import mimetypes
import os
import re
import shutil
import sys
from os.path import basename, dirname
from pathlib import Path
from typing import AnyStr, Optional

from clitt.core.term.cursor import Cursor
from hspylib.core.config.path_object import PathObject
from hspylib.core.enums.charset import Charset
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.core.tools.text_tools import ensure_endswith, strip_escapes
from hspylib.core.zoned_datetime import now_ms

from askai.core.support.text_formatter import text_formatter


def read_stdin() -> Optional[str]:
    """Read input from the standard input (stdin).
    :return: The input read from stdin as a string, or None if no input is provided.
    """
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def display_text(text: AnyStr, prefix: AnyStr = "", markdown: bool = True, erase_last=False) -> None:
    """Display the provided text in a formatted way.
    :param text: The text to be displayed.
    :param prefix: A prefix to prepend to the text (optional).
    :param markdown: Whether to render the text using markdown formatting (default is True).
    :param erase_last: Whether to erase the last displayed line before displaying the new text (default is False).
    """
    if erase_last:
        Cursor.INSTANCE.erase_line()
    if markdown:
        text_formatter.display_markdown(f"{str(prefix)}{text}")
    else:
        text_formatter.display_text(f"{str(prefix)}{text}")


def find_file(filename: AnyPath) -> Optional[Path]:
    """Find the specified file by name in the most common locations.
    :param filename: The name or path of the file to find.
    :return: The full path to the file if found, otherwise None.
    """
    prompt_path: Path = Path(filename) if filename else None
    if prompt_path and not prompt_path.exists():
        prompt_path = Path(os.path.expandvars(os.path.expanduser(filename)))
        if not prompt_path.exists():
            prompt_path = Path(os.path.join(os.getcwd(), filename))
            if not prompt_path.exists():
                prompt_path = Path(os.path.join(Path.home(), filename))
    return prompt_path if prompt_path and prompt_path.exists() else None


def copy_file(srcfile: AnyPath | Path, destfile: AnyPath | Path) -> str:
    """Copy the specified file to the given destination path.
    :param srcfile: The path of the source file to be copied.
    :param destfile: The destination path where the file should be copied.
    :return: The path of the copied file as a string.
    """
    filepath: PathObject = PathObject.of(srcfile)
    dest_dir: PathObject = PathObject.of(destfile)
    check_argument(filepath.exists and filepath.is_file and dest_dir.exists and dest_dir.is_dir)
    dest_file: str = os.path.join(dest_dir.abs_dir, filepath.filename)
    shutil.copy(srcfile, dest_file)
    return dest_file


def build_img_path(base_dir: Path, filename: str, suffix: str) -> Optional[str]:
    """Construct the full path for an image file based on the base directory, filename, and suffix.
    :param base_dir: The base directory where the image file is located.
    :param filename: The name of the image file (without the suffix).
    :param suffix: The suffix or extension to append to the filename (e.g., ".jpg", ".png").
    :return: The full path to the image file as a string, or None if the path cannot be constructed.
    """
    if not filename:
        return None
    img_path: str = str(Path.joinpath(base_dir, basename(filename or f"ASKAI-{now_ms()}"))).strip()
    img_path = re.sub(r"\s+", "-", ensure_endswith(img_path, suffix))
    img_path = re.sub(r"-+", "-", img_path)
    return strip_escapes(img_path)


def read_resource(base_dir: str, filename: str, file_ext: str = ".txt") -> str:
    """Read the resource file specified by the filename and return its content.
    :param base_dir: The base directory, relative to the resources folder.
    :param filename: The name of the file to read.
    :param file_ext: The file extension of the file (default is ".txt").
    :return: The content of the file as a string.
    """
    filename = f"{base_dir}/{ensure_endswith(basename(filename), file_ext)}"
    check_argument(file_is_not_empty(filename), f"Resource file is empty does not exist: {filename}")
    return Path(filename).read_text(encoding=Charset.UTF_8.val)


def encode_image(file_path: str):
    """Encode an image file to a base64 string.
    :param file_path: Path to the image file to be encoded.
    :return: Base64 encoded string of the image file.
    """
    with open(file_path, "rb") as f_image:
        return base64.b64encode(f_image.read()).decode(Charset.UTF_8.val)


def extract_path(command_line: str, flags: int = re.IGNORECASE | re.MULTILINE) -> Optional[str]:
    """Extract the first identifiable path from the provided command line text.
    :param command_line: The command line text from which to extract the path.
    :param flags: Regex match flags to control the extraction process (default is re.IGNORECASE | re.MULTILINE).
    :return: The first identified path as a string, or None if no path could be extracted.
    """
    command_line = re.sub("([12&]>|2>&1|1>&2).+", "", command_line.split("|")[0])
    re_path = r'(?:\w)\s+(?:-[\w\d]+\s)*(?:([\/\w\d\s"-]+)|(".*?"))'
    if command_line and (cmd_path := re.search(re_path, command_line, flags)):
        if (extracted := cmd_path.group(1).strip().replace("\\ ", " ")) and (_path_ := Path(extracted)).exists():
            if _path_.is_dir() or (extracted := dirname(extracted)):
                return extracted if extracted and Path(extracted).is_dir() else None
    return None


def extract_codeblock(text: str, flags: int = re.IGNORECASE | re.MULTILINE) -> tuple[Optional[str], str]:
    """Extract the programming language and actual code from a markdown multi-line code block.
    :param text: The markdown-formatted text containing the code block.
    :param flags: Regex match flags to control the extraction process (default is re.IGNORECASE | re.MULTILINE).
    :return: A tuple where the first element is the programming language (or None if not specified),
             and the second element is the extracted code as a string.
    """
    # Match a terminal command formatted in a markdown code block.
    re_command = r".*```((?:\w+)?\s*)\n(.*?)(?=^```)\s*\n?```.*"
    if text and (mat := re.search(re_command, text, flags=flags)):
        if mat and len(mat.groups()) == 2:
            lang, code = mat.group(1) or "", mat.group(2) or ""
            return lang, code
    return None, text


def strip_format(text: str) -> str:
    """Remove the markdown code block formatting from the text.
    :param text: The text containing the markdown code block formatting.
    :return: The text with the markdown code block formatting stripped away.
    """
    _, string = extract_codeblock(text)
    return strip_escapes(string)


def media_type_of(pathname: str) -> Optional[Optional[tuple[str, ...]]]:
    """Return the media type of the specified file, or None if the type could not be determined.
    :param pathname: The file path to check.
    :return: A tuple representing the media type (e.g., ("image", "jpeg")), or None if guessing was not possible.
    """
    mimetypes.init()
    mtype, _ = mimetypes.guess_type(basename(pathname))
    if mtype is not None:
        return tuple(mtype.split("/"))
    return None


def seconds(millis: int) -> float:
    """Convert milliseconds to seconds.
    :param millis: The time in milliseconds.
    :return: The equivalent time in seconds as a float.
    """
    return millis / 1000
