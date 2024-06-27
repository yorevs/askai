from textual_demos import events
from textual_demos.app import App, ComposeResult
from textual_demos.widgets import RichLog


class KeyLogger(RichLog):
    def on_key(self, event: events.Key) -> None:
        self.write(event)


class InputApp(App):
    """App to display key events."""

    CSS_PATH = "key_demo.tcss"

    def compose(self) -> ComposeResult:
        yield KeyLogger()
        yield KeyLogger()
        yield KeyLogger()
        yield KeyLogger()


if __name__ == "__main__":
    app = InputApp()
    app.run()
