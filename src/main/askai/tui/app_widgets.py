#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.tui.app_widgets
      @file: app_widgets.py
   @created: Mon, 29 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from textwrap import dedent
from typing import Callable, Optional

from askai.tui.app_icons import AppIcons
from rich.text import Text
from textual.app import ComposeResult, RenderResult
from textual.containers import Container
from textual.events import Click
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import Static, DataTable, Markdown, Collapsible


class MenuIcon(Widget):
    """Display an 'icon' on the left of the header."""

    DEFAULT_CSS = """
    MenuIcon {
      padding: 0 1;
      width: 4;
      content-align: center middle;
    }
    MenuIcon:hover {
      background: #7FD5AD 10%;
    }
    """

    menu_icon = AppIcons.DEFAULT.value

    def __init__(self, menu_icon: str, on_click: Optional[Callable] = None):
        super().__init__()
        self.menu_icon = menu_icon
        self.click_cb: Callable = on_click

    async def on_click(self, event: Click) -> None:
        """Launch the command palette when icon is clicked."""
        event.stop()
        if self.click_cb:
            self.click_cb()

    def render(self) -> RenderResult:
        """Render the header icon."""
        return self.menu_icon


class Splash(Container):
    """Splash widget that extends Container."""

    DEFAULT_CSS = """
    Splash {
      content-align: center middle;
      background: #030F12;
      width: 100%;
      height: 100%;
    }
    #splash {
      content-align: center middle;
      color: #7FD5AD;
      width: 100%;
      height: 100%;
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


class AppHelp(Markdown):
    """Application Help Widget."""

    DEFAULT_CSS = """
    AppHelp {
      align: center middle;
      display: block;
      visibility: visible;
    }
    """

    help_text: str

    def __init__(self, help_text: str):
        super().__init__()
        self.update(help_text)

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.set_class(True, "-hidden")


class AppInfo(Static):
    """Application Information Widget."""

    DEFAULT_CSS = """
    AppInfo {
      align: center middle;
      display: block;
      visibility: visible;
      Collapsible {
        color: #7FD5AD;
      }
    }
    #info {
      width: auto;
      height: auto;
      color: #FFFFFF;
      border: panel #183236;
      background: #030F12;
      color: #7FD5AD;
      content-align: left middle;
      padding: 2 1 1 1;
    }
    """

    info_text = reactive(True, repaint=True)

    credits: str = dedent(
        """
          Author:   Hugo Saporetti Junior
          GitHub:   https://github.com/yorevs/askai
        LinkedIn:   https://www.linkedin.com/in/yorevs/

          Thanks for using AskAI!
        """)

    def __init__(self, app_info: str):
        super().__init__()
        self.info_text = app_info

    @property
    def info(self) -> Static:
        """Get the Static widget."""
        return self.query_one("#info")

    def compose(self) -> ComposeResult:
        with Collapsible(title="Application Information", collapsed=False):
            yield Static(self.info_text, id="info")
        with Collapsible(title="Credits", collapsed=False):
            yield Static(self.credits)

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.set_class(True, "-hidden")

    async def watch_info_text(self) -> None:
        """TODO"""
        self.info.update(self.info_text)


class AppSettings(Static):
    """Application DataTable Widget."""

    DEFAULT_CSS = """
    AppSettings {
      align: center middle;
      display: block;
      visibility: visible;
      margin: 1 1 1 1;
    }
    #settings {
      margin-top: 1;
      width: auto;
      height: auto;
      border: panel #183236;
      background: #030F12;
      content-align: center middle;
    }
    """

    data = reactive(True, repaint=True)

    def __init__(self, data: list[tuple[str, ...]] = None):
        super().__init__()
        self.table = DataTable(id="settings")
        self.data = data or list()
        self.zebra_stripes = True

    def compose(self) -> ComposeResult:
        yield self.table

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.set_class(True, "-hidden")

    def watch_data(self) -> None:
        rows: list[tuple[str, ...]] = self.app.app_settings
        if rows:
            self.table.clear(True)
            self.table.add_columns(*rows[0])
            for i, row in enumerate(rows[1:], start=1):
                label = Text(str(i), style="#B0FC38 italic")
                self.table.add_row(*row, label=label)
            self.refresh()
