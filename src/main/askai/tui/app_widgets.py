#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.tui.app_widgets
      @file: app_widgets.py
   @created: Mon, 29 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import os
import re
import tempfile
from textwrap import dedent
from typing import Callable, Optional

from rich.text import Text
from textual import work
from textual.app import ComposeResult, RenderResult
from textual.containers import Container
from textual.events import Click
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Collapsible, DataTable, Markdown, Static, Input

from askai.core.commander.commands.history_cmd import HistoryCmd
from askai.core.commander.commands.tts_stt_cmd import TtsSttCmd
from askai.core.support.shared_instances import shared
from askai.tui.app_icons import AppIcons
from askai.tui.app_suggester import InputSuggester


class MenuIcon(Widget):
    """Display an 'icon' on the left of the header."""

    menu_icon = Reactive("")

    def __init__(
        self,
        menu_icon: str = AppIcons.DEFAULT.value,
        tooltip: str = None,
        on_click: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.menu_icon = menu_icon
        self.click_cb: Callable = on_click
        self.tooltip: str = tooltip

    async def on_click(self, event: Click) -> None:
        event.stop()
        if self.click_cb:
            self.click_cb()

    def render(self) -> RenderResult:
        return self.menu_icon


class Splash(Container):
    """Splash widget that extends Container."""

    splash_image: str = Reactive("")

    def __init__(self, splash_image: str):
        super().__init__()
        self.splash_image = splash_image

    def compose(self) -> ComposeResult:
        yield Static(self.splash_image, id="splash")

    async def on_mount(self) -> None:
        self.set_class(False, "-hidden")


class AppHelp(Markdown):
    """Application Help Widget."""

    help_text: str

    def __init__(self, help_text: str):
        super().__init__()
        self.update(help_text)

    async def on_mount(self) -> None:
        self.set_class(True, "-hidden")


class AppInfo(Static):
    """Application Information Widget."""

    info_text = Reactive("")
    credits: str = dedent(
        f"""
          Author:   Hugo Saporetti Junior
          GitHub:   https://github.com/yorevs/askai
        LinkedIn:   https://www.linkedin.com/in/yorevs/
            Demo:   https://www.youtube.com/watch?v=ZlVOisiUEvs&t=69s
        {'-' * 80}
          Thanks for using AskAI 
        """
    )

    def __init__(self, app_info: str = ""):
        super().__init__()
        self.info_text = app_info

    @property
    def info(self) -> Static:
        return self.query_one("#info")

    def compose(self) -> ComposeResult:
        with Collapsible(title="Application Information", collapsed=False):
            yield Static(self.info_text, id="info")
        with Collapsible(title="Credits", collapsed=False):
            yield Static(self.credits, id="credits")

    async def on_mount(self) -> None:
        self.set_class(True, "-hidden")

    async def watch_info_text(self) -> None:
        self.info.update(self.info_text)


class AppSettings(Static):
    """Application DataTable Widget."""

    data = Reactive("")

    def __init__(self, data: list[tuple[str, ...]] = None):
        super().__init__()
        self.table = DataTable(zebra_stripes=True, id="settings")
        self.data = data or list()

    def compose(self) -> ComposeResult:
        yield self.table

    async def on_mount(self) -> None:
        self.set_class(True, "-hidden")

    def watch_data(self) -> None:
        if self.data:
            self.table.clear(True)
            self.table.add_columns(*self.data[0][1:])
            for i, row in enumerate(self.data[1:], start=1):
                label = Text(str(i), style="#B0FC38 italic")
                self.table.add_row(*row[1:], key=row[0], label=label)
            self.refresh()


class InputArea(Widget):
    """Application Input Area."""

    def __init__(self, engine_nickname: str):
        super().__init__()
        self._engine_nickname = engine_nickname

    @property
    def engine_name(self) -> str:
        return self._engine_nickname

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        suggester = InputSuggester(case_sensitive=False)
        yield InputActions()
        yield Input(placeholder=f"Message {self.engine_name}", suggester=suggester)


class InputActions(Static):
    """Application Input Icons Area."""

    @staticmethod
    def copy() -> None:
        """TODO"""
        HistoryCmd.context_copy("LAST_REPLY")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield MenuIcon(AppIcons.READ_ALOUD.value, "Read aloud", self.read_aloud)
        yield MenuIcon(AppIcons.COPY_REPLY.value, "Copy", self.copy)
        # FIXME Uncomment after the rate functionality is ready
        # yield MenuIcon(AppIcons.LIKE.value, "Good response", self.like)
        # yield MenuIcon(AppIcons.DISLIKE.value, "Bad response", self.dislike)
        # yield MenuIcon(AppIcons.REGENERATE.value, "Regenerate response", self.regenerate)

    @work(thread=True)
    def read_aloud(self) -> None:
        """TODO"""
        if (ctx := str(shared.context.flat("LAST_REPLY"))) and (
            last_reply := re.sub(
                r"^((system|human|AI|assistant):\s*)", "", ctx, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE
            )
        ):
            TtsSttCmd.tts(last_reply.strip(), os.environ.get("TEMP", tempfile.gettempdir()), True)

    def submit(self) -> None:
        """TODO"""
        line_input: Input = self.app.line_input
        self.post_message(Input.Submitted(line_input, line_input.value))

    def like(self) -> None:
        """TODO"""
        pass

    def dislike(self) -> None:
        """TODO"""
        pass

    def regenerate(self) -> None:
        """TODO"""
        pass
