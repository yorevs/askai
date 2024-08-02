#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.settings_cmd
      @file: settings_cmd.py
   @created: Thu, 25 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from abc import ABC
from askai.core.askai_settings import settings
from askai.core.component.recorder import recorder
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text
from hspylib.core.tools.commons import sysout
from setman.settings.settings_entry import SettingsEntry
from typing import Any, Optional


class SettingsCmd(ABC):
    """Provides settings manipulation command functionalities."""

    @staticmethod
    def list(filters: str | None = None) -> None:
        """List all settings, optionally matching filters."""
        if all_settings := settings.search(f"*{filters}*"):
            sysout(all_settings + "\n")
        else:
            sysout(f"\n%RED%-=- No settings found! -=-%NC%\n")
        display_text(f"> Hint: Type: '/settings set \\<number|settings_name\\> \\<value\\>' to set.")

    @staticmethod
    def set(name: str, value: Any) -> None:
        """Set a setting value."""
        all_settings = settings.settings.search()
        if name.isdecimal() and 0 <= int(name) <= len(all_settings):
            name = all_settings[int(name)].name
        if settings[name]:
            settings.put(name, value if value not in ["''", '""'] else None)
            text_formatter.cmd_print(f"Setting `{name}` changed to %GREEN%{value}%NC%")
        else:
            text_formatter.cmd_print(f"%RED%Setting: '{name}' was not found!%NC%")

    @staticmethod
    def get(key: str) -> Optional[SettingsEntry]:
        """Get the setting specified by key."""
        if ss := settings[key]:
            text_formatter.cmd_print(f"%WHITE%Name: %BLUE%{ss.name}\t%WHITE%Value: %GREEN%{ss.value}%NC%")
            return ss
        text_formatter.cmd_print(f"%RED%Setting: '{key}' was not found!%NC%")
        return None

    @staticmethod
    def reset() -> None:
        """Reset settings to the defaults."""
        settings.defaults()
        # Include the current audio input.
        settings.put("askai.recorder.devices", recorder.input_device[1] or "")
