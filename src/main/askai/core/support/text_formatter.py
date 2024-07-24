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

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.text_tools import ensure_endswith, ensure_startswith
from hspylib.modules.cli.vt100.vt_code import VtCode
from hspylib.modules.cli.vt100.vt_color import VtColor
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from textwrap import dedent
from typing import Any

import os
import re


class TextFormatter(metaclass=Singleton):
    """TODO"""

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
    def ensure_ln(text: str) -> str:
        """Ensure text starts and ends with a lien separator.
        :param text: The text to be formatted.
        """
        return ensure_endswith(ensure_startswith(text, os.linesep), os.linesep * 2)

    def __init__(self):
        self._console: Console = Console()

    @property
    def console(self) -> Console:
        return self._console

    def beautify(self, text: Any) -> str:
        """Beautify the provided text with icons and other formatting improvements.
        :param text: The text to be beautified.
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

        # fmt: on

        return text

    def display_markdown(self, text: str) -> None:
        """Display a markdown formatted text.
        :param text: The text to be displayed.
        """
        colorized: str = VtColor.colorize(VtCode.decode(self.beautify(text)))
        self.console.print(Markdown(colorized))

    def display_text(self, text: str) -> None:
        """Display a vt100 formatted text.
        :param text: The text to be displayed.
        """
        colorized: str = VtColor.colorize(VtCode.decode(self.beautify(text)))
        self.console.print(Text.from_ansi(colorized))

    def cmd_print(self, text: str):
        """Display an AskAI commander text.
        :param text: The text to be displayed.
        """
        self.display_markdown(f"%ORANGE%  Commander%NC%: {self.beautify(text)}")


assert (text_formatter := TextFormatter().INSTANCE) is not None


if __name__ == "__main__":
    text_formatter.display_markdown(" Oops!\n>  An Exception Occurred: \n#### &nbsp;")
