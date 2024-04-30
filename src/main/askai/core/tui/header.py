from datetime import datetime

from rich.text import Text
from textual.app import RenderResult
from textual.events import Mount, Click
from textual.reactive import Reactive
from textual.widget import Widget


class HeaderIcon(Widget):
    """Display an 'icon' on the left of the header."""

    menu_icon = ""

    async def on_click(self, event: Click) -> None:
        """Launch the command palette when icon is clicked."""
        event.stop()
        await self.run_action("command_palette")

    def render(self) -> RenderResult:
        """Render the header icon."""
        return self.menu_icon


class AppInfoIcon(Widget):
    """Display an 'icon' on the left of the header."""

    menu_icon = ""

    def on_click(self, event: Click) -> None:
        """Launch the command palette when icon is clicked."""
        event.stop()
        self.app.info.toggle_class("-hidden")
        self.app.splash.toggle_class("-hidden")
        self.app.info.app_text = 'Updated text'

    def render(self) -> RenderResult:
        """Render the header icon."""
        return self.menu_icon


class HeaderTitle(Widget):
    """Display the title / subtitle in the header."""

    text: Reactive[str] = Reactive("")

    sub_text = Reactive("")

    def render(self) -> RenderResult:
        """Render the title and sub-title."""
        text = Text(self.text, no_wrap=True, overflow="ellipsis")
        if self.sub_text:
            text.append(" - ")
            text.append(self.sub_text)
        return text


class HeaderClockSpace(Widget):
    """The space taken up by the clock on the right of the header."""
    def render(self) -> RenderResult:
        """Render the header clock space."""
        return ""


class HeaderClock(HeaderClockSpace):
    """Display a clock on the right of the header."""
    def _on_mount(self, _: Mount) -> None:
        self.set_interval(1, callback=self.refresh, name=f"update header clock")

    def render(self) -> RenderResult:
        """Render the header clock."""
        return Text(datetime.now().time().strftime('%X'))


class Header(Widget):
    """A header widget with icon and clock."""

    def __init__(
        self,
        show_clock: bool = False,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        super().__init__(name=name, id=id, classes=classes)
        self._show_clock = show_clock

    def compose(self):
        yield HeaderIcon()
        yield HeaderTitle()
        yield HeaderClock() if self._show_clock else HeaderClockSpace()

    @property
    def screen_title(self) -> str:
        """The title that this header will display."""
        screen_title = self.screen.title
        title = screen_title if screen_title is not None else self.app.title
        return title

    @property
    def screen_sub_title(self) -> str:
        """The sub-title that this header will display."""
        screen_sub_title = self.screen.sub_title
        sub_title = (
            screen_sub_title if screen_sub_title is not None else self.app.sub_title
        )
        return sub_title

    def _on_mount(self, _: Mount) -> None:
        async def set_title() -> None:
            self.query_one(HeaderTitle).text = self.screen_title

        async def set_sub_title() -> None:
            self.query_one(HeaderTitle).sub_text = self.screen_sub_title

        self.watch(self.app, "title", set_title)
        self.watch(self.app, "sub_title", set_sub_title)
        self.watch(self.screen, "title", set_title)
        self.watch(self.screen, "sub_title", set_sub_title)
