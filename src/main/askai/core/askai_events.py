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

MIC_LISTENING_EVENT: str = "askai-mic-listening-event"

DEVICE_CHANGED_EVENT: str = "askai-input-device-changed-event"


class AskAiEvents(Enumeration):
    """Facility class to provide easy access to AskAI events."""

    @staticmethod
    class FluidEvent:
        """Provide a generic event interface."""

        def __init__(self, name: str, **kwargs):
            self.name = name
            for key, val in kwargs.items():
                setattr(self, key, val)

        def __str__(self):
            return f"FluidEvent-{self.name}::({', '.join(vars(self))})"

        def emit(self, bus_name: str, event_name: str, **kwargs) -> None:
            """Wrapper to the Event's emit method."""
            ...

        def subscribe(self, cb_event_handler: Callable) -> None:
            """Wrapper to the EventBus's subscribe method."""
            ...

    @staticmethod
    class FluidEventBus:
        """Provide a generic event bus interface."""

        def __init__(self, bus_name: str, **kwargs):
            self.name = bus_name
            self.bus = EventBus.get(bus_name)
            for key, evt in kwargs.items():
                fn_emit: Callable = partial(emit, bus_name, evt.name, **vars(evt))
                fn_subscribe: Callable = partial(self.bus.subscribe, evt.name, cb_event_handler=evt.cb_event_handler)
                setattr(evt, "emit", fn_emit)
                setattr(evt, "subscribe", fn_subscribe)
            self.events: Namespace = Namespace(f"FluidEventBus::{bus_name}", True, **kwargs)

        def __str__(self):
            return f"FluidEventBus-{self.bus.name}::({self.events})"

    # fmt: off
    ASKAI_BUS = FluidEventBus(
        ASKAI_BUS_NAME,
        reply=FluidEvent(REPLY_EVENT, verbosity='normal', erase_last=False, cb_event_handler=None),
        reply_error=FluidEvent(REPLY_ERROR_EVENT, cb_event_handler=None),
        listening=FluidEvent(MIC_LISTENING_EVENT, listening=True, cb_event_handler=None),
        device_changed=FluidEvent(DEVICE_CHANGED_EVENT, device=None, cb_event_handler=None),
    )
    # fmt: on

    @staticmethod
    def bus(bus_name: str) -> Optional[FluidEventBus]:
        """Return an eventbus instance for the given name."""
        return next((b.bus for b in AskAiEvents.values() if b.name == bus_name), None)

    def __init__(self, bus: FluidEventBus):
        self._bus = bus

    @property
    def events(self) -> Namespace:
        return self.value.events
