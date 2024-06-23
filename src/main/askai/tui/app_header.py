#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.tui.header
      @file: app_header.py
   @created: Mon, 29 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_configs import configs
from askai.core.component.recorder import recorder
from askai.tui.app_icons import AppIcons
from askai.tui.app_widgets import MenuIcon
from hspylib.core.zoned_datetime import now
from rich.text import Text
from textual.app import RenderResult
from textual.events import Mount
from textual.reactive import Reactive
from textual.widget import Widget


class Header(Widget):
    """A header widget with icon and notifications."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def notifications(self):
        return self.query_one(HeaderNotifications)

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
        sub_title = screen_sub_title if screen_sub_title is not None else self.app.sub_title
        return sub_title

    def compose(self):
        """Compose the Header Widget."""
        yield MenuIcon(AppIcons.TOC.value, "Show/Hide Table of Contents", self.app.action_toggle_table_of_contents)
        yield MenuIcon(AppIcons.CONSOLE.value, "Show console", self._show_console)
        yield MenuIcon(AppIcons.SETTINGS.value, "Show settings", self._show_settings)
        yield MenuIcon(AppIcons.INFO.value, "Show application information", self._show_info)
        yield MenuIcon(AppIcons.HELP.value, "Show application help", self._show_help)
        yield HeaderTitle()
        yield HeaderNotifications()

    def _on_mount(self, _: Mount) -> None:
        async def set_title() -> None:
            """The title that this header will display."""
            self.query_one(HeaderTitle).text = self.screen_title

        async def set_sub_title() -> None:
            """The sub-title that this header will display."""
            self.query_one(HeaderTitle).sub_text = self.screen_sub_title

        self.watch(self.app, "title", set_title)
        self.watch(self.app, "sub_title", set_sub_title)
        self.watch(self.screen, "title", set_title)
        self.watch(self.screen, "sub_title", set_sub_title)

    def _show_help(self) -> None:
        """Handle the header menu 'help' clicks."""
        self.app.help.set_class(False, "-hidden")
        self.app.info.set_class(True, "-hidden")
        self.app.md_console.set_class(True, "-hidden")
        self.app.settings.set_class(True, "-hidden")

    def _show_settings(self) -> None:
        """Handle the header menu 'settings' clicks."""
        self.app.settings.set_class(False, "-hidden")
        self.app.help.set_class(True, "-hidden")
        self.app.info.set_class(True, "-hidden")
        self.app.md_console.set_class(True, "-hidden")

    def _show_info(self) -> None:
        """Handle the header menu 'info' clicks."""
        self.app.info.set_class(False, "-hidden")
        self.app.help.set_class(True, "-hidden")
        self.app.md_console.set_class(True, "-hidden")
        self.app.settings.set_class(True, "-hidden")

    def _show_console(self) -> None:
        """Handle the header menu 'console' clicks."""
        self.app.activate_markdown()
        self.app.help.set_class(True, "-hidden")
        self.app.info.set_class(True, "-hidden")
        self.app.settings.set_class(True, "-hidden")


class HeaderTitle(Widget):
    """Display the title / subtitle in the header."""

    text = Reactive("")
    sub_text = Reactive("")

    def render(self) -> RenderResult:
        """Render the title and sub-title."""
        text = Text(self.text, no_wrap=True, overflow="ellipsis")
        if self.sub_text:
            text.append(f"  {AppIcons.SEPARATOR_H}  ")
            text.append(str(self.sub_text))
        return text


class HeaderNotifications(Widget):
    """Display a notification widget on the right of the header."""

    speaking = Reactive(configs.is_speak)
    debugging = Reactive(configs.is_debug)
    listening = Reactive(False)
    headphones = Reactive(False)

    def __init__(self):
        super().__init__()

    def _on_mount(self, _: Mount) -> None:
        self.set_interval(1, callback=self.refresh, name="update clock")
        self.set_interval(0.5, callback=self.refresh_icons, name="update icons")

    def render(self) -> RenderResult:
        """Render the header notifications."""
        return Text(
            f"{AppIcons.HEADPHONES if self.headphones else AppIcons.BUILT_IN_SPEAKER}  "
            f"{AppIcons.LISTENING_ON if self.listening else AppIcons.LISTENING_OFF}  "
            f"{AppIcons.SPEAKING_ON if self.speaking else AppIcons.SPEAKING_OFF} "
            f"{AppIcons.DEBUG_ON if self.debugging else AppIcons.DEBUG_OFF}  "
            f"{AppIcons.SEPARATOR_V} {now(f'%a %d %b  %X')}"
        )

    def refresh_icons(self) -> None:
        """Update the application widgets. This callback is required because ask_and_reply is async."""
        self.headphones = recorder.is_headphones()
        self.debugging = self.app.is_debugging
        self.speaking = self.app.is_speak
        self.app.info.info_text = str(self.app)
        self.app.settings.data = self.app.app_settings

    async def watch_speaking(self) -> None:
        self.refresh()

    async def watch_debugging(self) -> None:
        self.refresh()

    async def watch_listening(self) -> None:
        self.refresh()

    async def watch_headphones(self) -> None:
        self.refresh()
