import os
from functools import partial
from typing import Optional

from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.namespace import Namespace
from hspylib.modules.eventbus.eventbus import EventBus, emit

ASKAI_BUS_NAME: str = "askai-reply-bus"

REPLY_EVENT: str = "askai-reply-event"

REPLY_ERROR_EVENT: str = "askai-reply-error-event"


class AskAiEvents(Enumeration):
    """TODO"""

    @staticmethod
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

    @staticmethod
    class _EventBus:
        """Provide a generic event bus interface."""

        def __init__(self, bus_name: str, **kwargs):
            self.name = bus_name
            self.bus = EventBus.get(bus_name)
            for key, evt in kwargs.items():
                setattr(evt, 'emit', partial(emit, bus_name, evt.name, **vars(evt)))
            self.events = Namespace(f"AskAi-EventBus::{bus_name}", True, **kwargs)

        def __str__(self):
            return f"_EventBus-{self.bus.name}::({self.events})"

    # fmt: off
    ASKAI_BUS = _EventBus(
        ASKAI_BUS_NAME,
        reply=_Event(REPLY_EVENT, erase_last=False),
        reply_error=_Event(REPLY_EVENT)
    )

    # fmt: on

    @staticmethod
    def get_bus(bus_name: str) -> Optional[EventBus]:
        """TODO"""
        return next((b.bus for b in AskAiEvents.values() if b.name == bus_name), None)

    def __init__(self, bus: _EventBus):
        self._bus = bus

    @property
    def events(self) -> Namespace:
        return self.value.events
