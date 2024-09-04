"""
   @project: HsPyLib-AskAI
   @package: askai.core.support.text_formatter
      @file: text_formatter.py
   @created: Fri, 28 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from clitt.core.term.cursor import cursor
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.text_tools import ensure_endswith, ensure_startswith, strip_escapes
from hspylib.modules.cli.vt100.vt_code import VtCode
from hspylib.modules.cli.vt100.vt_color import VtColor
from textwrap import dedent
from typing import Any, AnyStr

import os
import re


class TextFormatter(metaclass=Singleton):
    """A utility class for formatting text according to specified rules or styles.
    This class provides various methods for transforming and formatting text,
    such as adjusting indentation, line breaks, or applying specific text styles.
    The Singleton metaclass ensures that only one instance of this class exists throughout the application.
    """

    INSTANCE: "TextFormatter"

    RE_URL = (
        r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s')]{2,}|"
        r"www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s')]{2,}|https?:\/\/(?:www\.|(?!www))"
        r"[a-zA-Z0-9]+\.[^\s')]{2,}|www\.[a-zA-Z0-9]+\.[^\s')]{2,})"
    )

    RE_MD_CODE_BLOCK = r"(```.+```)"

    CHAT_ICONS = {
        "": " Oops!\n>  An Exception Occurred: \n####  ",
        "": "\n>   *Tip:* ",
        "": "\n>   *Analysis:* ",
        "": "\n>   *Summary:* ",
        "": "\n>   *Joke:* ",
        "": "\n>   *Fun-Fact:* ",
        "": "\n>   *Advice:* ",
        "﬽": "\n> ﬽  *Conclusion:* ",
    }

    RE_TYPES = {
        "MD": RE_MD_CODE_BLOCK,
        "": RE_URL,
        "": r"[\s*_]*Errors?[_*-:\s]+",
        "": r"[\s*_]*Hints?( ([Aa]nd|&) [Tt]ips?)?[_*-:\s]+",
        "": r"[\s*_]*Analysis[_*-:\s]+",
        "": r"[\s*_]*Summary[_*-:\s]+",
        "": r"[\s*_]*Fun[\s-]+[Ff]acts?[_*-:\s]+",
        "": r"[\s*_]*(Jokes?(\s+[Tt]ime)?)[_*-:\s]+",
        "": r"[\s*_]*Advice[_*-:\s]+",
        "﬽": r"[\s*_]*Conclusion[_*-:\s]+",
    }

    @staticmethod
    def ensure_ln(text: str, separator: str = os.linesep) -> str:
        """Ensure the text starts and ends with a line separator.
        :param text: The text to be formatted.
        :param separator: The line separator to use (default is the system's line separator).
        :return: The formatted text with the specified line separator at the beginning and end.
        """
        return ensure_endswith(ensure_startswith(text, separator), separator * 2)

    def beautify(self, text: Any) -> str:
        """Beautify the provided text with icons and other formatting enhancements.
        :param text: The text to be beautified.
        :return: The beautified text as a string with applied icons and formatting improvements.
        """
        # fmt: off

        text = dedent(str(text))
        text = re.sub(self.RE_TYPES[''], self.CHAT_ICONS[''], text)
        text = re.sub(self.RE_TYPES[''], self.CHAT_ICONS[''], text)
        text = re.sub(self.RE_TYPES[''], self.CHAT_ICONS[''], text)
        text = re.sub(self.RE_TYPES[''], self.CHAT_ICONS[''], text)
        text = re.sub(self.RE_TYPES[''], self.CHAT_ICONS[''], text)
        text = re.sub(self.RE_TYPES[''], self.CHAT_ICONS[''], text)
        text = re.sub(self.RE_TYPES[''], self.CHAT_ICONS[''], text)
        text = re.sub(self.RE_TYPES['﬽'], self.CHAT_ICONS['﬽'], text)
        # Improve links
        text = re.sub(self.RE_TYPES[''], r" [\1](\1)", text)
        # Make sure markdown is prefixed and suffixed with new lines
        text = re.sub(self.RE_TYPES['MD'], r"\n\1\n", text)
        text = re.sub(r'```(.+)```\s+', r"\n```\1```\n", text)

        # fmt: on

        return text

    def display_markdown(self, text: AnyStr) -> None:
        """Display a markdown-formatted text.
        :param text: The markdown-formatted text to be displayed.
        """
        colorized: str = VtColor.colorize(VtCode.decode(self.beautify(str(text))))
        cursor.write(colorized, markdown=True)

    def display_text(self, text: AnyStr) -> None:
        """Display a VT100 formatted text.
        :param text: The VT100 formatted text to be displayed.
        """
        colorized: str = VtColor.colorize(VtCode.decode(self.beautify(str(text))))
        cursor.write(colorized)

    def cmd_print(self, text: AnyStr):
        """Display an AskAI commander formatted text.
        :param text: The text to be displayed.
        """
        self.display_markdown(f"%ORANGE%  Commander%NC%: {self.beautify(str(text))}")

    def remove_markdown(self, text: AnyStr) -> str:
        """
        Remove Markdown formatting from a string.
        """
        plain_text = re.sub(r'```(.*?)```', r'\1', str(text), flags=re.DOTALL)
        plain_text = re.sub(r'`[^`]+`', '', plain_text)
        plain_text = re.sub(r'^(#+\s+)', '', plain_text)
        plain_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', plain_text)
        plain_text = re.sub(r'\*([^*]+)\*', r'\1', plain_text)
        plain_text = re.sub(r'__([^_]+)__', r'\1', plain_text)
        plain_text = re.sub(r'_([^_]+)_', r'\1', plain_text)
        plain_text = re.sub(r'\[([^]]+)]\([^)]+\)', r'\1', plain_text)
        plain_text = re.sub(r'!\[([^]]*)]\([^)]+\)', r'\1', plain_text)
        plain_text = re.sub(r'---|___|\*\*\*', '', plain_text)
        plain_text = re.sub(r'>\s+', '', plain_text)
        plain_text = re.sub(r'[-*+]\s+', '', plain_text)
        plain_text = re.sub(r'^\d+\.\s+', '', plain_text)

        return plain_text.strip()

    def strip_format(self, text: AnyStr) -> str:
        """Remove the markdown code block formatting from the text.
        :param text: The text containing the markdown code block formatting.
        :return: The text with the markdown code block formatting stripped away.
        """
        return strip_escapes(self.remove_markdown(text))


assert (text_formatter := TextFormatter().INSTANCE) is not None
