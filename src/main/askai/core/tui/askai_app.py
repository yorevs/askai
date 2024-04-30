import os
from pathlib import Path

from cachetools import LRUCache
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.text_tools import ensure_endswith
from hspylib.modules.application.version import Version
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.reactive import var
from textual.suggester import SuggestFromList
from textual.widgets import Footer, MarkdownViewer, Input

from askai.__classpath__ import classpath
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
    ]

    SPLASH_IMAGE: str = classpath.get_resource("splash.txt").read_text(encoding=Charset.UTF_8.val)

    APP_INFO: str = "Just some app info"

    CONSOLE_FILE: Path = Path(f"{CACHE_DIR}/askai-output.md")

    if not CONSOLE_FILE.exists():
        CONSOLE_FILE.touch()

    PATH = var(CONSOLE_FILE)

    def __init__(self):
        super().__init__()
        self.input_history = ['/help', '/settings', '/voices', '/debug']

    @property
    def md_console(self) -> MarkdownViewer:
        """Get the MarkdownViewer widget."""
        return self.query_one(MarkdownViewer)

    @property
    def splash(self) -> Splash:
        """Get the Splash widget."""
        return self.query_one(Splash)

    @property
    def info(self) -> AppInfo:
        """Get the AppInfo widget."""
        return self.query_one(AppInfo)

    @property
    def line_input(self) -> Input:
        """Get the Input widget."""
        return self.query_one(Input)

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        suggester = SuggestFromList(self.input_history, case_sensitive=False)
        suggester.cache = LRUCache(1024)
        yield Header()
        with ScrollableContainer():
            yield AppInfo(self.APP_INFO)
            yield Splash(self.SPLASH_IMAGE)
            yield MarkdownViewer()
        yield Input(
            placeholder="Message chatGPT",
            suggester=suggester
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.md_console.set_classes("-hidden")
        self.screen.title = f"AskAI v{Version.load(load_dir=classpath.source_path())}"
        self.screen.sub_title = "ChatGPT"

    async def activate_markdown(self) -> None:
        self.md_console.set_classes("-visible")
        self.md_console.focus()
        self.md_console.show_table_of_contents = True
        await self.md_console.go(self.PATH)

    async def display_text(self, markdown_text: str) -> None:
        with open(self.CONSOLE_FILE, 'a', encoding=Charset.UTF_8.val) as f_console:
            f_console.write(f"{ensure_endswith(markdown_text, os.linesep * 2)}")
        await self.md_console.go(self.PATH)

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """A coroutine to handle a text changed message."""
        self.line_input.clear()
        await self.display_text(message.value)


if __name__ == "__main__":
    app = AskAI()
    app.run()
