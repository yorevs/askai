#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.askai_events
      @file: askai_events.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.namespace import Namespace
from hspylib.modules.eventbus.fluid import FluidEvent, FluidEventBus
from typing import Optional

ASKAI_BUS_NAME: str = "askai-reply-bus"

REPLY_EVENT: str = "askai-reply-event"

REPLY_ERROR_EVENT: str = "askai-reply-error-event"

MIC_LISTENING_EVENT: str = "askai-mic-listening-event"

DEVICE_CHANGED_EVENT: str = "askai-input-device-changed-event"

MODE_CHANGED_EVENT: str = "askai-routing-mode-changed-event"


class AskAiEvents(Enumeration):
    """Facility class to provide easy access to AskAI events."""

    # fmt: off
    ASKAI_BUS = FluidEventBus(
        ASKAI_BUS_NAME,
        reply=FluidEvent(REPLY_EVENT, verbosity='normal', erase_last=False),
        reply_error=FluidEvent(REPLY_ERROR_EVENT),
        listening=FluidEvent(MIC_LISTENING_EVENT, listening=True),
        device_changed=FluidEvent(DEVICE_CHANGED_EVENT, device=None),
        mode_changed=FluidEvent(MODE_CHANGED_EVENT, mode=None, sum_path=None, glob=None),
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


events: Namespace = AskAiEvents.ASKAI_BUS.events
