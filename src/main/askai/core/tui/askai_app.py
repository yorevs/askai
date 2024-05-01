import os
import uuid
from asyncio import sleep
from pathlib import Path
from random import randint

from cachetools import LRUCache
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.text_tools import ensure_endswith
from hspylib.modules.application.version import Version
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.suggester import SuggestFromList
from textual.widgets import MarkdownViewer, Input, Footer

from askai.__classpath__ import classpath
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import CACHE_DIR
from askai.core.tui.app_widgets import Splash, AppInfo
from askai.core.tui.header import Header

SOURCE_DIR: Path = classpath.source_path()

RESOURCE_DIR: Path = classpath.resource_path()


class AskAI(App):
    """The AskAI Textual app."""

    CSS_PATH = f"{RESOURCE_DIR}/askai.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear", "Clear Console"),
    ]

    SPLASH_IMAGE: str = classpath.get_resource("splash.txt").read_text(encoding=Charset.UTF_8.val)

    def __init__(self):
        super().__init__()
        self._session_id = str(uuid.uuid4()).replace('-', '')[:8]
        self._input_history = ['/help', '/settings', '/voices', '/debug']
        self._console_path = Path(f"{CACHE_DIR}/askai-{self.session_id}.md")
        if not self._console_path.exists():
            self._console_path.touch()

    @property
    def nickname(self) -> str:
        return f"*  Taius*"

    @property
    def username(self) -> str:
        return f"**  {prompt.user.title()}**"

    @property
    def md_console(self) -> MarkdownViewer:
        """Get the MarkdownViewer widget."""
        return self.query_one(MarkdownViewer)

    @property
    def info(self) -> AppInfo:
        """Get the AppInfo widget."""
        return self.query_one(AppInfo)

    @property
    def splash(self) -> Splash:
        """Get the Splash widget."""
        return self.query_one(Splash)

    @property
    def line_input(self) -> Input:
        """Get the Input widget."""
        return self.query_one(Input)

    @property
    def header(self) -> Header:
        """Get the Input widget."""
        return self.query_one(Header)

    @property
    def footer(self) -> Footer:
        """Get the Input widget."""
        return self.query_one(Footer)

    @property
    def session_id(self) -> str:
        """Get the Session id."""
        return self._session_id

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        suggester = SuggestFromList(self._input_history, case_sensitive=False)
        suggester.cache = LRUCache(1024)
        yield Header(id="header")
        with ScrollableContainer(id="container"):
            yield AppInfo("")
            yield Splash(self.SPLASH_IMAGE)
            yield MarkdownViewer()
        yield Input(
            id="input",
            placeholder=f"Message ChatGPT",
            suggester=suggester
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.screen.title = f"AskAI v{Version.load(load_dir=classpath.source_path())}"
        self.screen.sub_title = "GPT-3.5"
        self.header.disabled = True
        self.line_input.disabled = True
        self.footer.disabled = True
        self.md_console.set_class(True, "-hidden")
        self._startup()

    async def activate_markdown(self) -> None:
        """Activate the Markdown console."""
        self.md_console.set_classes("-visible")
        self.md_console.focus()
        self.md_console.show_table_of_contents = True
        await self.md_console.go(self._console_path)

    async def display_text(self, markdown_text: str) -> None:
        """Send the text to the Markdown console."""
        with open(self._console_path, 'a', encoding=Charset.UTF_8.val) as f_console:
            f_console.write(f"{ensure_endswith(markdown_text, os.linesep * 2)}")
        await self.md_console.go(self._console_path)

    @on(Input.Submitted)
    async def on_submit(self, message: Input.Submitted) -> None:
        """A coroutine to handle a input submission."""
        self.line_input.clear()
        await self.display_text(f"{self.username}: {message.value.title()}")

    async def action_clear(self) -> None:
        """TODO"""
        open(self._console_path, 'w', encoding=Charset.UTF_8.val).close()
        await self.md_console.go(self._console_path)

    @work
    async def _startup(self) -> None:
        await sleep(randint(2, 10))
        self.header.disabled = False
        self.line_input.disabled = False
        self.footer.disabled = False
        await self.activate_markdown()
        self.splash.set_class(True, "-hidden")
        self.info.info_text = "Some usefull information"
        self.line_input.focus()
        await self.display_text(f"{self.nickname}: {msg.welcome(prompt.user.title())}")


if __name__ == "__main__":
    app = AskAI()
    app.run()
