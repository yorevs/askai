import os
from functools import partial

from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.namespace import Namespace
from hspylib.modules.eventbus.eventbus import EventBus, emit

from askai.language.language import Language
from askai.utils.constants import Constants


class AskAiEvents(Enumeration):
    """TODO"""

    class _Event:
        """Provide a generic event interface."""

        def __init__(self, name: str, **kwargs):
            self.name = name
            for key, val in kwargs.items():
                setattr(self, key, val)

        def __str__(self):
            return f"_Event-{self.name}::({', '.join(vars(self))})"

        def emit(self, bus_name: str, event_name: str, **kwargs) -> None:
            pass

    class _EventBus:
        """Provide a generic event bus interface."""

        def __init__(self, bus_name: str, **kwargs):
            self.bus = EventBus.get(bus_name)
            for key, evt in kwargs.items():
                setattr(evt, 'emit', partial(emit, bus_name, evt.name, **vars(evt)))
            self.events = Namespace(f"AskAi-EventBus::{bus_name}", True, **kwargs)

        def __str__(self):
            return f"_EventBus-{self.bus.name}::({self.events})"

    # fmt: off
    DISPLAY_BUS = _EventBus(
        Constants.DISPLAY_BUS,
        display=_Event(Constants.DISPLAY_EVENT, end=os.linesep, erase_last=False),
        stream=_Event(Constants.STREAM_EVENT, tempo=1, lang=Language.EN_US),
        terminate=_Event(Constants.TERM_EVENT)
    )

    CAPTURER_BUS = _EventBus(
        Constants.CAPTURER_BUS,
        stdoutCaptured=_Event(Constants.STDOUT_CAPTURED),
        stderrCaptured=_Event(Constants.STDERR_CAPTURED)
    )
    # fmt: on

    def __init__(self, bus: _EventBus):
        self._bus = bus

    @property
    def events(self) -> Namespace:
        return self.value.events
