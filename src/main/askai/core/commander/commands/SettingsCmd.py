from abc import ABC
from typing import Any

from askai.core.askai_settings import settings
from askai.core.component.recorder import recorder
from hspylib.core.tools.commons import sysout


class SettingsCmd(ABC):
    """TODO"""

    def __init__(self):
        pass

    @staticmethod
    def list(filters: str | None = None) -> None:
        """TODO"""
        sysout(settings.search(f"*{filters}*"))

    @staticmethod
    def set(key: str, value: Any) -> None:
        """TODO"""
        if settings[key]:
            settings.put(key, value)
        else:
            sysout(f"\n%RED%Setting: '{key}' was not found!%NC%\n")

    @staticmethod
    def get(key: str) -> None:
        """TODO"""
        if ss := settings[key]:
            sysout(f"\n%WHITE%Name: %BLUE%{ss.name}\t%WHITE%Value: %GREEN%{ss.value}%NC%\n")
        else:
            sysout(f"\n%RED%Setting: '{key}' was not found!%NC%\n")

    @staticmethod
    def reset() -> None:
        """TODO"""
        settings.defaults()
        # Include the current audio input.
        settings.put("askai.recorder.devices", recorder.input_device[1] or '')
