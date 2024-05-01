from datetime import datetime

from rich.text import Text
from textual.app import RenderResult
from textual.events import Mount
from textual.reactive import Reactive
from textual.widget import Widget

from askai.core.tui.app_icons import AppIcons
from askai.core.tui.app_widgets import MenuIcon


class HeaderTitle(Widget):
    """Display the title / subtitle in the header."""

    text: Reactive[str] = Reactive("")

    sub_text = Reactive("")

    def render(self) -> RenderResult:
        """Render the title and sub-title."""
        text = Text(self.text, no_wrap=True, overflow="ellipsis")
        if self.sub_text:
            text.append(" - ")
            text.append(str(self.sub_text))
        return text


class HeaderClock(Widget):
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
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        super().__init__(name=name, id=id, classes=classes)

    def compose(self):
        yield MenuIcon(AppIcons.MENU.value, self._show_menu)
        yield MenuIcon(AppIcons.INFO.value, self._show_info)
        yield MenuIcon(AppIcons.CONSOLE.value, self._show_console)
        yield HeaderTitle()
        yield HeaderClock()

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
            """TODO"""
            self.query_one(HeaderTitle).text = self.screen_title

        async def set_sub_title() -> None:
            """TODO"""
            self.query_one(HeaderTitle).sub_text = self.screen_sub_title

        self.watch(self.app, "title", set_title)
        self.watch(self.app, "sub_title", set_sub_title)
        self.watch(self.screen, "title", set_title)
        self.watch(self.screen, "sub_title", set_sub_title)

    async def _show_menu(self) -> None:
        await self.run_action("command_palette")

    async def _show_info(self) -> None:
        self.app.info.set_class(False, "-hidden")
        self.app.md_console.set_class(True, "-hidden")

    async def _show_console(self) -> None:
        self.app.info.set_class(True, "-hidden")
        await self.app.activate_markdown()
