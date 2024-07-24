#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.component.scheduler
      @file: scheduler.py
   @created: Thu, 25 Mar 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from datetime import datetime, timedelta
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_argument
from threading import Thread
from time import monotonic
from typing import Any, Callable, Iterable, Mapping

import pause
import threading


class Scheduler(Thread, metaclass=Singleton):
    """Provide a scheduler class."""

    INSTANCE: "Scheduler"

    _done = False

    def __init__(self):
        super().__init__()
        self._today = datetime.today()
        self._threads: list[Thread] = []
        self._start_time = monotonic()

    @staticmethod
    def every(interval_ms: int, delay_ms: int):
        """Decorate a function to be run every `interval_ms` seconds. Can't be used to decorate instance
        methods (with self). For that use the `set_interval` method."""

        def every_wrapper(func: Callable, *fargs, **fkwargs):
            """every wrapper"""
            return scheduler.set_interval(interval_ms, func, delay_ms, *fargs, **fkwargs)

        return every_wrapper

    @staticmethod
    def at(hour: int, minute: int, second: int, millis: int):
        """Decorate a function to run at a specific time. Can't be used to decorate instance
        methods (with self). For that use the `schedule` method."""

        def at_wrapper(func: Callable, *fargs, **fkwargs):
            """at wrapper"""
            return scheduler.schedule(hour, minute, second, millis, func, *fargs, **fkwargs)

        return at_wrapper

    def run(self) -> None:
        while not self._done and threading.main_thread().is_alive():
            not_started = next((th for th in self._threads if not th.is_alive()), None)
            if not_started:
                not_started.start()
                self._threads.remove(not_started)
            pause.milliseconds(500)

    def start(self) -> None:
        if not self.is_alive():
            super().start()

    def schedule(
        self,
        hh: int,
        mm: int,
        ss: int,
        us: int,
        callback: Callable,
        cb_fn_args: Iterable | None = None,
        cb_fn_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        """Schedule a task to run at specific time in future.
        :param hh: The hour of the day.
        :param mm: The minute of the day.
        :param ss: The seconds of the day.
        :param us: The microseconds of the day.
        :param callback: The callback function.
        :param cb_fn_args: The arguments of the callback function.
        :param cb_fn_kwargs: The keyword arguments of the callback function.
        """
        run_at: datetime = self._today.replace(day=self._today.day, hour=hh, minute=mm, second=ss, microsecond=us)
        delta_t: timedelta = run_at - self._today
        check_argument(delta_t.total_seconds() > 0, ">> Time is in the past <<")
        secs: float = max(0, delta_t.seconds) + 1

        def __timer():
            while not self._done and threading.main_thread().is_alive():
                elapsed = monotonic() - self._start_time
                if elapsed >= secs:
                    args = cb_fn_args if cb_fn_args else []
                    xargs = cb_fn_kwargs if cb_fn_kwargs else {}
                    callback(*args, **xargs)
                    return
                pause.milliseconds(100)

        self._threads.append(Thread(name=f"Scheduled-{callback.__name__}", target=__timer))

    def set_interval(
        self,
        interval_ms: int,
        callback: Callable,
        delay_ms: int = 0,
        cb_fn_args: Iterable | None = None,
        cb_fn_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        """Schedule a task to run every interval in milliseconds.
        :param interval_ms: The interval in milliseconds, to invoke the callback function.
        :param callback: The callback function.
        :param delay_ms: The initial delay before start invoking.
        :param cb_fn_args: The arguments of the callback function.
        :param cb_fn_kwargs: The keyword arguments of the callback function.
        """

        def __task():
            if delay_ms > 0:
                pause.milliseconds(interval_ms)
            while not self._done and threading.main_thread().is_alive():
                args = cb_fn_args if cb_fn_args else []
                xargs = cb_fn_kwargs if cb_fn_kwargs else {}
                callback(*args, **xargs)
                pause.milliseconds(interval_ms)

        self._threads.append(Thread(name=f"Interval-{callback.__name__}", target=__task))


assert (scheduler := Scheduler().INSTANCE) is not None
