from pathlib import Path

from hspylib.core.enums.charset import Charset
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Container
from textual.reactive import var
from textual.widgets import Header, Footer, MarkdownViewer, Static

from askai.__classpath__ import classpath

SOURCE_DIR: Path = classpath.source_path()

RESOURCE_DIR: Path = classpath.resource_path()


class Splash(Container):
    """Splash widget that extends Container."""

    SPLASH_IMAGE: str = (RESOURCE_DIR / "splash.txt").read_text(encoding=Charset.UTF_8.val)

    CSS_PATH = f"{RESOURCE_DIR}/askai.tcss"

    def compose(self) -> ComposeResult:
        yield Static(self.SPLASH_IMAGE, id="splash")


class AskAI(App):
    """The AskAI Textual app."""

    CSS_PATH = f"{RESOURCE_DIR}/askai.tcss"

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    path = var(Path(__file__).parent / f"{SOURCE_DIR}/../README.md")

    @property
    def markdown_viewer(self) -> MarkdownViewer:
        """Get the Markdown widget."""
        return self.query_one(MarkdownViewer)

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Header()
        yield Footer()
        yield ScrollableContainer(Splash())

    # async def on_mount(self) -> None:
    #     """Called application is mounted."""
    #     self.markdown_viewer.focus()
    #     self.markdown_viewer.show_table_of_contents = False
    #     try:
    #         await self.markdown_viewer.go(self.path)
    #     except FileNotFoundError:
    #         self.exit(message=f"Unable to load {self.path!r}")


if __name__ == "__main__":
    app = AskAI()
    app.run()
