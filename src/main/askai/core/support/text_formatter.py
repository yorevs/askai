"""
   @project: HsPyLib-AskAI
   @package: askai.core.support.text_formatter
      @file: text_formatter.py
   @created: Fri, 28 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
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

    CHAT_ICONS = {
        "": "*An exception occurred*: \n> ",
        "": "\n>   *TIP*: ",
        "": "\n>   *Analysis*: ",
        "": "\n>   *Summary*: ",
        "": "\n>   *Joke*: ",
        "": "\n>   *Fun-Fact*: ",
        "": "\n>   *Advice*: ",
        "﬽": "\n> ﬽  *Conclusion*: ",
    }

    @staticmethod
    def ensure_ln(text: str) -> str:
        """TODO"""
        return ensure_endswith(ensure_startswith(text.strip(), os.linesep), os.linesep * 2)

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
        re_url = (
            r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s')]{2,}|"
            r"www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s')]{2,}|https?:\/\/(?:www\.|(?!www))"
            r"[a-zA-Z0-9]+\.[^\s')]{2,}|www\.[a-zA-Z0-9]+\.[^\s')]{2,})"
        )
        text = dedent(str(text))
        text = re.sub(r"[\s*_]*Errors?[_*-:\s]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"[\s*_]*Hints?( (and|&) [Tt]ips?)?[_*-:\s]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"[\s*_]*Analysis[_*-:\s]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"[\s*_]*Summary[_*-:\s]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"[\s*_]*Fun[\s-]+[Ff]acts?[_*-:\s]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"[\s*_]*(Jokes?(\s+[Tt]ime)?)[_*-:\s]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"[\s*_]*Advice[_*-:\s]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"[\s*_]*Conclusion[_*-:\s]+", self.CHAT_ICONS['﬽'], text)
        text = re.sub(re_url, r' [\1](\1)', text)
        text = re.sub(r'(`{3}.+`{3})', r'\n\1\n', text)
        # fmt: on

        return text

    def display_markdown(self, text: str) -> None:
        """TODO"""
        colorized: str = VtColor.colorize(VtCode.decode(self.beautify(text).strip()))
        self.console.print(Markdown(colorized))

    def display_text(self, text: str) -> None:
        """TODO"""
        colorized: str = VtColor.colorize(VtCode.decode(self.beautify(text).strip()))
        self.console.print(Text.from_ansi(colorized))

    def cmd_print(self, text: str):
        """TODO"""
        self.display_markdown(f"%ORANGE%  Commander%NC%: {self.beautify(text).strip()}")


assert (text_formatter := TextFormatter().INSTANCE) is not None


if __name__ == '__main__':
    print(text_formatter.beautify("Error: this is an error"))
    print(text_formatter.beautify("*Error*: this is an error"))
    print(text_formatter.beautify("**Error**: this is an error"))
    print(text_formatter.beautify("**Errors**: this is an error"))
    print(text_formatter.beautify("Hint: this is a hint"))
    print(text_formatter.beautify("*Hint*: this is a hint"))
    print(text_formatter.beautify("**Hint**: this is a hint"))
    print(text_formatter.beautify("**Hints**: this is a hint"))
    print(text_formatter.beautify("Joke: this is a joke"))
    print(text_formatter.beautify("*Joke*: this is a joke"))
    print(text_formatter.beautify("**Joke**: this is a joke"))
    print(text_formatter.beautify("**Jokes**: this is a joke"))
    print(text_formatter.beautify("Analysis: this is an analysis"))
    print(text_formatter.beautify("*Analysis*: this is an analysis"))
    print(text_formatter.beautify("**Analysis**: this is an analysis"))
    print(text_formatter.beautify("Fun Fact: this is a fun fact"))
    print(text_formatter.beautify("Fun-Fact: this is a fun fact"))
    print(text_formatter.beautify("*Fun Fact*: this is a fun fact"))
    print(text_formatter.beautify("*Fun-Fact*: this is a fun fact"))
    print(text_formatter.beautify("**Fun Fact**: this is a fun fact"))
    print(text_formatter.beautify("**Fun-Fact**: this is a fun fact"))
    print(text_formatter.beautify("_Fun-Fact_: this is a fun fact"))
    print(text_formatter.beautify("__Fun  Fact__: this is a fun fact"))
