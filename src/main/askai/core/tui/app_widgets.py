from typing import Callable, Optional

from textual.app import ComposeResult, RenderResult
from textual.events import Click, Event
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Static

from askai.core.tui.app_icons import AppIcons


class MenuIcon(Widget):
    """Display an 'icon' on the left of the header."""

    menu_icon: Reactive[str] = AppIcons.DEFAULT.value

    def __init__(self, menu_icon: str, on_click: Optional[Callable] = None):
        super().__init__()
        self.menu_icon = menu_icon
        self.click_cb: Callable[[Event], None] = on_click

    async def on_click(self, event: Click) -> None:
        """Launch the command palette when icon is clicked."""
        event.stop()
        if self.click_cb:
            await self.click_cb()

    def render(self) -> RenderResult:
        """Render the header icon."""
        return self.menu_icon


class Splash(Static):
    """Splash widget that extends Container."""

    DEFAULT_CSS = """
    Splash {
      align: center middle;
      display: block;
      visibility: visible;
    }

    Splash.-hidden {
      display: none;
      visibility: hidden;
    }
    """

    splash_image: str = Reactive("")

    def __init__(self, splash_image: str):
        super().__init__()
        self.splash_image = splash_image

    def compose(self) -> ComposeResult:
        yield Static(self.splash_image, id="splash")

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.set_class(False, "-hidden")


class AppInfo(Static):
    """Information widget."""

    DEFAULT_CSS = """
    AppInfo {
      align: center middle;
      display: block;
      visibility: visible;
    }

    AppInfo.-hidden {
      display: none;
      visibility: hidden;
    }
    """

    app_info: Reactive[str] = Reactive("")

    def __init__(self, app_info: str):
        super().__init__()
        self.app_info = app_info

    def compose(self) -> ComposeResult:
        yield Static(self.app_info, id="info")

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.set_class(True, "-hidden")
