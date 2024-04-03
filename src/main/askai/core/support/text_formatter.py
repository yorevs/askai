import re
from textwrap import dedent
from typing import Any

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.dict_tools import get_or_default
from hspylib.modules.cli.vt100.vt_code import VtCode
from hspylib.modules.cli.vt100.vt_color import VtColor
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text


class TextFormatter(metaclass=Singleton):
    """TODO"""

    INSTANCE: "TextFormatter" = None

    CHAT_ICONS = {
        "": "\n%RED%  Error: ",
        "": "\n>   *TIP:* ",
        "": "\n>   *Analysis:* ",
        "": "\n>   *Summary:* ",
        "": "\n>   *Joke:* ",
        "": "\n>   *Fun-Fact:* ",
        "": "\n>   *Advice:* ",
    }

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
        text = re.sub(r"\**Errors?[-:\s][\s*]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"\**[Hh]ints?( (and|&) [Tt]ips)?[-:\s][\s*]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"\**[Aa]nalysis[-:\s][\s*]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"\**[Ss]ummary[-:\s][\s*]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"\**[Ff]un [Ff]acts?[-:\s][\s*]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"\**([Jj]oke( [Tt]ime)?)[-:\s][\s*]+", self.CHAT_ICONS[''], text)
        text = re.sub(r"\**[Aa]dvice[-:\s][\s*]+", self.CHAT_ICONS[''], text)
        fg = get_or_default(re.findall(r"%\w+%", text), 0, '%NC%')
        text = re.sub(re_url, r' [\1](\1)', text)
        text = re.sub(r'(`{3}.+`{3})', r'\n\1\n', text)
        # fmt: on

        return text.strip()

    def display_markdown(self, text: str) -> None:
        colorized: str = VtColor.colorize(VtCode.decode(self.beautify(text)))
        self.console.print(Markdown(colorized))

    def display_text(self, text: str) -> None:
        colorized: str = VtColor.colorize(VtCode.decode(self.beautify(text)))
        self.console.print(Text.from_ansi(colorized))


assert (text_formatter := TextFormatter().INSTANCE) is not None
