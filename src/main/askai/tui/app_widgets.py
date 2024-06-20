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

from typing import Callable, Optional

from textual.app import ComposeResult, RenderResult
from textual.containers import Container
from textual.events import Click
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import Static

from askai.tui.app_icons import AppIcons


class MenuIcon(Widget):
    """Display an 'icon' on the left of the header."""

    DEFAULT_CSS = """
    MenuIcon {
      padding: 0 1;
      width: 4;
      content-align: left middle;
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
      background: #030F12;
      width: 100%;
      height: 95%;
      padding: 0 0;
      margin: 5 0;
    }
    #splash {
      content-align: center middle;
      color: #7FD5AD;
      background: #030F12;
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
    """Application Information Widget."""

    DEFAULT_CSS = """
    AppInfo {
      align: center middle;
      display: block;
      visibility: visible;
    }
    """

    info_text = reactive(True, repaint=True)

    def __init__(self, app_info: str):
        super().__init__()
        self.info_text = app_info

    @property
    def info(self) -> Static:
        """Get the Static widget."""
        return self.query_one(Static)

    def compose(self) -> ComposeResult:
        yield Static(self.info_text, id="info")

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.set_class(True, "-hidden")

    async def watch_info_text(self) -> None:
        """TODO"""
        self.info.update(self.info_text)


class AppSettings(Widget):
    """Application Settings Widget."""

    DEFAULT_CSS = """
    AppSettings {
      align: center middle;
      display: block;
      visibility: visible;
    }
    """

    settings_text = reactive(True, repaint=True)

    def __init__(self, settings: str):
        super().__init__()
        self.settings_text = settings

    @property
    def settings(self) -> Static:
        """Get the Static widget."""
        return self.query_one(Static)

    def compose(self) -> ComposeResult:
        yield Static(self.settings_text, id="settings")

    async def on_mount(self) -> None:
        """Called application is mounted."""
        self.set_class(True, "-hidden")

    async def watch_settings_text(self) -> None:
        """TODO"""
        self.settings.update(self.settings_text)
