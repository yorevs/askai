#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.askai_events
      @file: askai_events.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from functools import partial
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.namespace import Namespace
from hspylib.modules.eventbus.eventbus import emit, EventBus
from typing import Callable, Optional

ASKAI_BUS_NAME: str = "askai-reply-bus"

REPLY_EVENT: str = "askai-reply-event"

REPLY_ERROR_EVENT: str = "askai-reply-error-event"


class AskAiEvents(Enumeration):
    """Facility class to provide easy access to AskAI events."""

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

        def subscribe(self, cb_event_handler: Callable) -> None:
            pass

    @staticmethod
    class _EventBus:
        """Provide a generic event bus interface."""

        def __init__(self, bus_name: str, **kwargs):
            self.name = bus_name
            self.bus = EventBus.get(bus_name)
            for key, evt in kwargs.items():
                setattr(evt, "emit", partial(emit, bus_name, evt.name, **vars(evt)))
                setattr(evt, "subscribe", partial(self.bus.subscribe, evt.name, cb_event_handler=evt.cb_event_handler))
            self.events = Namespace(f"AskAi-EventBus::{bus_name}", True, **kwargs)

        def __str__(self):
            return f"_EventBus-{self.bus.name}::({self.events})"

    # fmt: off
    ASKAI_BUS = _EventBus(
        ASKAI_BUS_NAME,
        reply=_Event(REPLY_EVENT, verbosity='normal', erase_last=False, cb_event_handler=None),
        reply_error=_Event(REPLY_ERROR_EVENT, cb_event_handler=None)
    )

    # fmt: on

    @staticmethod
    def get_bus(bus_name: str) -> Optional[EventBus]:
        """Return an eventbus instance for the given name."""
        return next((b.bus for b in AskAiEvents.values() if b.name == bus_name), None)

    def __init__(self, bus: _EventBus):
        self._bus = bus

    @property
    def events(self) -> Namespace:
        return self.value.events
