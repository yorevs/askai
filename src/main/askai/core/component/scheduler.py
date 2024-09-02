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
    """A singleton scheduler class for managing and executing scheduled tasks.
    Inherits from:
        - Thread: Allows the scheduler to run tasks in a separate thread.
    """

    INSTANCE: "Scheduler"

    _done = False

    def __init__(self):
        super().__init__()
        self._today = datetime.today()
        self._threads: list[Thread] = []
        self._start_time = monotonic()

    @staticmethod
    def every(interval_ms: int, delay_ms: int):
        """Decorator to schedule a function to be run periodically. The decorated function will be executed every
        `interval_ms` milliseconds, with an initial delay of `delay_ms` milliseconds before the first execution.
        Note:
            - This decorator cannot be used for instance methods (methods with `self`).
            - For scheduling instance methods, use the `set_interval` method.
        :param interval_ms: The interval in milliseconds between consecutive executions of the decorated function.
        :param delay_ms: The initial delay in milliseconds before the first execution of the decorated function.
        :return: The decorated function.
        """
        def every_wrapper(func: Callable, *fargs, **fkwargs):
            """'every' function wrapper."""
            return scheduler.set_interval(interval_ms, func, delay_ms, *fargs, **fkwargs)

        return every_wrapper

    @staticmethod
    def at(hour: int, minute: int, second: int, millis: int):
        """Decorator to schedule a function to be run periodically at a specific time each day. This decorator
        schedules the decorated function to execute at the given hour, minute, second, and millisecond every day. It is
        useful for tasks that need to be performed at a specific time daily.
        Note:
            - This decorator cannot be used to decorate instance methods (with `self`). For instance methods,
              use the `schedule` method.
        :param hour: The hour of the day (0-23) when the function should run.
        :param minute: The minute of the hour (0-59) when the function should run.
        :param second: The second of the minute (0-59) when the function should run.
        :param millis: The millisecond of the second (0-999) when the function should run.
        :return: A decorator that schedules the function to run at the specified time.
        """

        def at_wrapper(func: Callable, *fargs, **fkwargs):
            """'at' function wrapper."""
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
        """Schedule a task to run at a specific time in the future. This method schedules the provided callback
        function to execute at the specified hour, minute, second, and microsecond on the current day. The function
        will be invoked with the specified arguments and keyword arguments.
        :param hh: The hour of the day (0-23) when the task should run.
        :param mm: The minute of the hour (0-59) when the task should run.
        :param ss: The second of the minute (0-59) when the task should run.
        :param us: The microsecond of the second (0-999999) when the task should run.
        :param callback: The callback function to be executed at the scheduled time.
        :param cb_fn_args: The positional arguments to pass to the callback function. Defaults to None.
        :param cb_fn_kwargs: The keyword arguments to pass to the callback function. Defaults to None.
        """
        run_at: datetime = self._today.replace(day=self._today.day, hour=hh, minute=mm, second=ss, microsecond=us)
        delta_t: timedelta = run_at - self._today
        check_argument(delta_t.total_seconds() > 0, ">> Time is in the past <<")
        secs: float = max(0, delta_t.seconds) + 1

        def _call_it_back():
            """Continuously checks if the scheduled time has been reached and executes the callback function. The
            method uses a 100ms pause between checks to avoid excessive CPU usage.
            """
            while not self._done and threading.main_thread().is_alive():
                elapsed = monotonic() - self._start_time
                if elapsed >= secs:
                    args = cb_fn_args if cb_fn_args else []
                    xargs = cb_fn_kwargs if cb_fn_kwargs else {}
                    callback(*args, **xargs)
                    return
                pause.milliseconds(100)

        self._threads.append(Thread(name=f"Schedule-{callback.__name__}", target=_call_it_back))

    def set_interval(
        self,
        interval_ms: int,
        callback: Callable,
        delay_ms: int = 0,
        cb_fn_args: Iterable | None = None,
        cb_fn_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        """Schedule a function to be run periodically at a specified interval (in milliseconds). This method schedules
        the given callback function to be invoked repeatedly at the specified interval in milliseconds. The function
        will be initially delayed by the specified amount of milliseconds before the first invocation.
        :param interval_ms: The interval in milliseconds between each invocation of the callback function.
        :param callback: The callback function to be invoked periodically.
        :param delay_ms: The initial delay in milliseconds before starting the periodic invocations.
        :param cb_fn_args: The arguments to pass to the callback function.
        :param cb_fn_kwargs: The keyword arguments to pass to the callback function.
        """
        def _call_it_back():
            """Internal method to repeatedly invoke the callback function at specified intervals. It uses the
            `pause.milliseconds()` method to handle the waiting periods between each invocation.
            """
            if delay_ms > 0:
                pause.milliseconds(interval_ms)
            while not self._done and threading.main_thread().is_alive():
                args = cb_fn_args if cb_fn_args else []
                xargs = cb_fn_kwargs if cb_fn_kwargs else {}
                callback(*args, **xargs)
                pause.milliseconds(interval_ms)

        self._threads.append(Thread(name=f"SetInterval-{callback.__name__}", target=_call_it_back))


assert (scheduler := Scheduler().INSTANCE) is not None
