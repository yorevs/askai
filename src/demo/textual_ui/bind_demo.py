from textual_ui.app import App, ComposeResult
from textual_ui.color import Color
from textual_ui.widgets import Footer, Static


class Bar(Static):
    pass


class BindingApp(App):
    CSS_PATH = "bind_demo.tcss"
    BINDINGS = [
        ("r", "add_bar('red')", "Add Red"),
        ("g", "add_bar('green')", "Add Green"),
        ("b", "add_bar('blue')", "Add Blue"),
    ]

    def compose(self) -> ComposeResult:
        yield Footer()

    def action_add_bar(self, color: str) -> None:
        bar = Bar(color)
        bar.styles.background = Color.parse(color).with_alpha(0.5)
        self.mount(bar)
        self.call_after_refresh(self.screen.scroll_end, animate=False)


if __name__ == "__main__":
    app = BindingApp()
    app.run()
