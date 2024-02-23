import os
from functools import partial

from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.namespace import Namespace
from hspylib.modules.eventbus.eventbus import EventBus, emit

from askai.language.language import Language
from askai.utils.constants import Constants


class AskAiEvents(Enumeration):

    class _Evt:

        def __init__(self, name: str, **kwargs):
            self.name = name
            for key, val in kwargs.items():
                setattr(self, key, val)

        def __str__(self):
            return f"_Evt::({', '.join(vars(self))})"

    class _EvtBus:

        def __init__(self, bus_name: str, **kwargs):
            self.bus = EventBus.get(bus_name)
            for key, evt in kwargs.items():
                setattr(evt, 'emit', partial(emit, bus_name, evt.name, **vars(evt)))
            self.events = Namespace(f"_EvtBus::{bus_name}", True, **kwargs)

        def __str__(self):
            return f"AskAiBus::({self.events})"

    # fmt: off
    DISPLAY_BUS = _EvtBus(
        Constants.DISPLAY_BUS,
        display=_Evt(Constants.DISPLAY_EVENT, end=os.linesep, erase_last=False),
        stream=_Evt(Constants.STREAM_EVENT, tempo=1, lang=Language.EN_US),
        terminate=_Evt(Constants.TERM_EVENT)
    )
    # fmt: on

    """TODO"""
    def __init__(self, bus: _EvtBus):
        self._bus = bus

    @property
    def events(self) -> Namespace:
        return self.value.events

