from pathlib import Path

from hspylib.core.enums.charset import Charset
from hspylib.modules.application.version import Version
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.reactive import var
from textual.widgets import Footer, MarkdownViewer, Input

from askai.__classpath__ import classpath
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

    path = var(Path(__file__).parent / f"{SOURCE_DIR}/../README.md")

    def __init__(self):
        super().__init__()
        self.title = f"AskAI v{Version.load(load_dir=classpath.source_path())}"
        self.sub_title = "ChatGPT"

    @property
    def markdown_viewer(self) -> MarkdownViewer:
        """Get the Markdown widget."""
        return self.query_one(MarkdownViewer)

    @property
    def splash(self) -> Splash:
        """Get the Splash widget."""
        return self.query_one(Splash)

    @property
    def info(self) -> AppInfo:
        """Get the Splash widget."""
        return self.query_one(AppInfo)

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Header(show_clock=True)
        with ScrollableContainer():
            yield AppInfo("Just some app info")
            yield Splash(self.SPLASH_IMAGE)
            yield MarkdownViewer()
        yield Input(placeholder="Message chatGPT")
        yield Footer()

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.markdown_viewer.set_classes("-hidden")

    async def activate_markdown(self) -> None:
        self.markdown_viewer.set_classes("-visible")
        self.markdown_viewer.focus()
        self.markdown_viewer.show_table_of_contents = False
        try:
            await self.markdown_viewer.go(self.path)
        except FileNotFoundError:
            self.exit(message=f"Unable to load {self.path!r}")


if __name__ == "__main__":
    app = AskAI()
    app.run()
