from textual.app import ComposeResult
from textual.reactive import Reactive
from textual.widgets import Static


class Splash(Static):
    """Splash widget that extends Container."""

    # icons:                          婢    鬒

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
