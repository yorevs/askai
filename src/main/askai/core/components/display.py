#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.components
      @file: display.py
   @created: Wed, 21 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import os
from threading import Thread

import pause
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import sysout
from hspylib.modules.eventbus.event import Event
from hspylib.modules.eventbus.eventbus import EventBus, subscribe, emit


class Display(metaclass=Singleton):
    """TODO"""

    INSTANCE = None

    def __init__(self):
        self._done = False
        self._queue = []
        self._streaming = False
        self._display_thread = Thread(
            daemon=True, target=self._run
        )
        self._display_thread.start()

    def _run(self) -> None:
        """TODO"""
        while not self._done:
            try:
                if next_text := self._queue.pop():
                    self._display(next_text)
                else:
                    pause.milliseconds(100)
            except IndexError:
                pause.milliseconds(100)
                continue

    @staticmethod
    @subscribe(bus="display-bus", event="display-event")
    def _enqueue(ev: Event) -> None:
        """TODO"""
        Display.INSTANCE._queue.append(ev.args.text)

    def _display(self, text: str, end: str = os.linesep) -> None:
        """TODO"""
        while self._streaming:
            pause.milliseconds(100)
        sysout(text, end=end)

    def _stream(self, text: str) -> None:
        """TODO"""
        pass


assert Display().INSTANCE is not None


if __name__ == '__main__':
    d = Display.INSTANCE
    bus = EventBus.get("display-bus")
    emit("display-bus", "display-event", text="First displayed text!!!")
    emit("display-bus", "display-event", text="Second displayed text!!!")
    pause.seconds(5)
