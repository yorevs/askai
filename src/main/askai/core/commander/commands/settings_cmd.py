from abc import ABC
from typing import Any, Optional

from askai.core.askai_settings import settings
from askai.core.component.recorder import recorder
from askai.core.support.text_formatter import text_formatter
from hspylib.core.tools.commons import sysout
from setman.settings.settings_entry import SettingsEntry

from askai.core.support.utilities import display_text


class SettingsCmd(ABC):
    """TODO"""

    @staticmethod
    def list(filters: str | None = None) -> None:
        """TODO"""
        if all_settings := settings.search(f"*{filters}*"):
            sysout(all_settings)
            display_text(f"\n> Hint: Type: '/settings set \\<number|settings_name\\> \\<value\\>' to set.")
        else:
            sysout(f"\n%RED%-=- No settings found! -=-%NC%\n")

    @staticmethod
    def set(name: str, value: Any) -> None:
        """TODO"""
        all_settings = settings.settings.search()
        if name.isdecimal() and 0 <= int(name) <= len(all_settings):
            name = all_settings[int(name)].name
        if settings[name]:
            settings.put(name, value)
            text_formatter.cmd_print(f"Setting `{name}` changed to %GREEN%{value}%NC%")
        else:
            text_formatter.cmd_print(f"%RED%Setting: '{name}' was not found!%NC%")

    @staticmethod
    def get(key: str) -> Optional[SettingsEntry]:
        """TODO"""
        if ss := settings[key]:
            text_formatter.cmd_print(f"%WHITE%Name: %BLUE%{ss.name}\t%WHITE%Value: %GREEN%{ss.value}%NC%")
            return ss
        text_formatter.cmd_print(f"%RED%Setting: '{key}' was not found!%NC%")
        return None

    @staticmethod
    def reset() -> None:
        """TODO"""
        settings.defaults()
        # Include the current audio input.
        settings.put("askai.recorder.devices", recorder.input_device[1] or '')
