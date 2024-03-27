import re
from random import randint
from textwrap import dedent
from typing import Any

from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import sysout
from hspylib.modules.cli.vt100.vt_code import VtCode
from hspylib.modules.cli.vt100.vt_color import VtColor
from rich.console import Console
from rich.highlighter import RegexHighlighter, Highlighter
from rich.markdown import Markdown


class TextFormatter(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'TextFormatter' = None

    CHAT_ICONS = {
        '': '\n%RED%  Error: ',
        '': '\n>   *Hints & Tips:* ',
        '': '\n>   *Analysis:* ',
        '': '\n>   *Summary:* ',
        '': '\n>   *Joke:* ',
        '': '\n>   *Fun-Fact:* ',
        '': '\n>   *Advice:* ',
    }

    def __init__(self):
        self._console: Console = Console(soft_wrap=True)

    @property
    def console(self) -> Console:
        return self._console

    def beautify(self, text: Any) -> str:
        """Beautify the provided text with icons and other formatting improvements.
        :param text: The text to be beautified.
        """
        # fmt: off
        re_url = (
            r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|'
            r'www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))'
            r'[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})'
        )
        text = dedent(str(text))
        text = re.sub(r"Errors?[-:\s]\s+", self.CHAT_ICONS[''], text)
        text = re.sub(r"[Hh]ints?( (and|&) [Tt]ips)?[-:\s]\s+", self.CHAT_ICONS[''], text)
        text = re.sub(r"[Aa]nalysis[-:\s]\s+", self.CHAT_ICONS[''], text)
        text = re.sub(r"[Ss]ummary[-:\s]\s+", self.CHAT_ICONS[''], text)
        text = re.sub(r"[Ff]un [Ff]acts?[-:\s]\s+", self.CHAT_ICONS[''], text)
        text = re.sub(r"([Jj]oke( [Tt]ime)?)[-:\s]\s+", self.CHAT_ICONS[''], text)
        text = re.sub(r"[Aa]dvice[-:\s]\s+", self.CHAT_ICONS[''], text)
        mat = re.search(r"%\w+%", text)
        fg = mat.group() if mat else ''
        text = re.sub(re_url, r' \1', text)
        # fmt: on

        return text.strip()

    def display_markdown(self, text: str) -> None:
        colorized: str = VtColor.colorize(VtCode.decode(self.beautify(text)))
        self.console.print(Markdown(colorized), highlight=True)

    def display_text(self, text: str) -> None:
        sysout(self.beautify(text))


assert (text_formatter := TextFormatter().INSTANCE) is not None


class RainbowHighlighter(Highlighter):
    def highlight(self, text):
        for index in range(len(text)):
            text.stylize(f"color({randint(16, 255)})", index, index + 1)


class Highlighter(RegexHighlighter):
    base_style = "help."
    highlights = [r"(?P<cmd>!help\b)", r"(?P<cmd2>\'|\"[\w]+\"|\')"]


if __name__ == '__main__':
    s = dedent("""
    Error: This should be red
    Advice: This should be yellow
    Hint: This should be blue
    Joke: This should be magenta
    Analysis: This should be yellow

    This is not OK because it has failed to be a success!

    For more details access: https://askai.github.io/askai Enjoy!
    """)
    text_formatter.display_markdown(s)
