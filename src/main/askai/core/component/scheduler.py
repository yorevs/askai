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
from functools import wraps
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_argument
from hspylib.core.zoned_datetime import SIMPLE_DATETIME_FORMAT
from threading import Thread
from time import monotonic
from typing import Any, Callable, Iterable, Mapping

import inspect
import os
import pause
import threading


class Scheduler(Thread, metaclass=Singleton):
    """A singleton scheduler class for managing and executing scheduled tasks.
    Inherits from:
        - Thread: Allows the scheduler to run tasks in a separate thread.
    """

    INSTANCE: "Scheduler"

    _DONE: bool = False

    @staticmethod
    def every(interval_ms: int, delay_ms: int = 0):
        """
        Decorator to schedule a function to be run periodically. The decorated function will be executed every
        `interval_ms` milliseconds, with an initial delay of `delay_ms` milliseconds before the first execution.
        Can be used with both instance methods (methods with `self`) and static or standalone functions.

        :param interval_ms: The interval in milliseconds between consecutive executions of the decorated function.
        :param delay_ms: The initial delay in milliseconds before the first execution of the decorated function.
        :return: The decorated function.
        """

        def helper(func: Callable):
            """Wrapper to handle both instance methods and static functions."""

            @wraps(func)
            def wrapped_function(*args, **kwargs):
                # Check if the first argument is likely to be 'self' (i.e., method bound to an instance)
                if len(args) > 0 and inspect.isclass(type(args[0])):
                    self = args[0]  # The first argument is 'self'
                    return scheduler.set_interval(interval_ms, func, delay_ms, self, *args[1:], **kwargs)
                else:
                    # It's either a static method or a standalone function
                    return scheduler.set_interval(interval_ms, func, delay_ms, *args, **kwargs)

            return wrapped_function()

        return helper

    @staticmethod
    def at(hour: int, minute: int, second: int, millis: int = 0):
        """
        Decorator to schedule a function to be run periodically at a specific time each day. This can handle both
        instance methods (with `self`) and standalone functions.

        :param hour: The hour of the day (0-23) when the function should run.
        :param minute: The minute of the hour (0-59) when the function should run.
        :param second: The second of the minute (0-59) when the function should run.
        :param millis: The millisecond of the second (0-999) when the function should run.
        :return: A decorator that schedules the function to run at the specified time.
        """

        def helper(func: Callable):
            """Wrapper to handle both instance methods and static functions."""

            @wraps(func)
            def wrapped_function(*args, **kwargs):
                # Check if the first argument is likely to be 'self' (i.e., method bound to an instance)
                if len(args) > 0 and inspect.isclass(type(args[0])):
                    self = args[0]  # The first argument is 'self'
                    return scheduler.schedule(hour, minute, second, millis, func, self, *args[1:], **kwargs)
                else:
                    # It's either a static method or a standalone function
                    return scheduler.schedule(hour, minute, second, millis, func, *args, **kwargs)

            return wrapped_function()

        return helper

    @staticmethod
    def after(hour: int = 0, minute: int = 0, second: int = 0, microsecond: int = 0):
        """
        Decorator to schedule a function to be run after the specified hour, minute, second, and microsecond delay.
        Can be used for both instance methods (with `self`) and static or standalone functions.

        :param hour: Hours to delay
        :param minute: Minutes to delay
        :param second: Seconds to delay
        :param microsecond: Microseconds to delay
        :return: A decorator that schedules the function to run after the specified delay.
        """

        def helper(func: Callable):
            """Wrapper to handle both instance methods and static functions."""

            @wraps(func)
            def wrapped_function(*args, **kwargs):
                # Check if the first argument is likely to be 'self' (i.e., method bound to an instance)
                if len(args) > 0 and inspect.isclass(type(args[0])):
                    self = args[0]  # The first argument is 'self'
                    return scheduler.scheduler_after(hour, minute, second, microsecond, func, self, *args[1:], **kwargs)
                else:
                    # It's either a static method or a standalone function
                    return scheduler.scheduler_after(hour, minute, second, microsecond, func, *args, **kwargs)

            return wrapped_function()

        return helper

    def __init__(self):
        super().__init__()
        self._relief_interval_ms: int = 100
        self._now: datetime = datetime.now()
        self._not_started: list[Thread] = []
        self._threads: dict[str, Thread] = {}
        self._start_time: float = monotonic()

    def __str__(self):
        return (
            f"Started: {self.now.strftime(SIMPLE_DATETIME_FORMAT)}\n"
            f"jobs:\n"
            f"{'  |-' + '  |-'.join([j + os.linesep for j, _ in self._threads.items()]) if self._threads else '<none>'}"
        )

    @property
    def now(self) -> datetime:
        return self._now

    @property
    def alive(self) -> bool:
        return not self._DONE and threading.main_thread().is_alive()

    def run(self) -> None:
        while self.alive:
            if not_started := next((th for th in self._not_started if not th.is_alive()), None):
                not_started.start()
                self._remove(not_started)
            pause.milliseconds(self._relief_interval_ms)

    def start(self) -> None:
        if not self.is_alive():
            super().start()
            self._now = datetime.now()

    def schedule(
        self,
        hour: int,
        minute: int,
        second: int,
        microsecond: int,
        callback: Callable,
        cb_fn_args: Iterable | None = None,
        cb_fn_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        """Schedule a task to run at a specific time in the future. This method schedules the provided callback
        function to execute at the specified hour, minute, second, and microsecond on the current day. The function
        will be invoked with the specified arguments and keyword arguments.
        :param hour: The hour of the day (0-23) when the task should run.
        :param minute: The minute of the hour (0-59) when the task should run.
        :param second: The second of the minute (0-59) when the task should run.
        :param microsecond: The microsecond of the second (0-999999) when the task should run.
        :param callback: The callback function to be executed at the scheduled time.
        :param cb_fn_args: The positional arguments to pass to the callback function. Defaults to None.
        :param cb_fn_kwargs: The keyword arguments to pass to the callback function. Defaults to None.
        """
        run_at: datetime = self.now.replace(
            day=self.now.day, hour=hour, minute=minute, second=second, microsecond=microsecond
        )
        delta_t: timedelta = run_at - self.now
        check_argument(delta_t.total_seconds() > 0, ">> Time is in the past <<")
        secs: float = max(0, delta_t.seconds) + 1

        def _call_it_back() -> None:
            """Continuously checks if the scheduled time has been reached and executes the callback function. The
            method uses a pause between checks to avoid excessive CPU usage.
            """
            while self.alive:
                if monotonic() - self._start_time >= secs:
                    args = cb_fn_args if cb_fn_args else []
                    xargs = cb_fn_kwargs if cb_fn_kwargs else {}
                    callback(*args, **xargs)
                    return
                pause.milliseconds(self._relief_interval_ms)

        self._add(f"Scheduled-{callback.__name__}", _call_it_back)

    def scheduler_after(
        self,
        hh: int,
        mm: int,
        ss: int,
        us: int,
        callback: Callable,
        cb_fn_args: Iterable | None = None,
        cb_fn_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        """Schedule a function to be run after the specified hour, minute, second, and microsecond.
        :param hh: Hours to delay
        :param mm: Minutes to delay
        :param ss: Seconds to delay
        :param us: microsecond delay
        :param callback: Function to be executed
        :param cb_fn_args: Optional arguments to pass to the callback function
        :param cb_fn_kwargs: Optional keyword arguments to pass to the callback function
        """
        check_argument(any(num > 0 for num in [hh, mm, ss]), ">> Delay must be positive <<")
        # fmt: off
        delta_t: timedelta = timedelta(hours=hh, minutes=mm, seconds=ss, microseconds=us)
        # fmt: on
        run_at: datetime = self.now + delta_t
        self.schedule(run_at.hour, run_at.minute, run_at.second, run_at.microsecond, callback, cb_fn_args, cb_fn_kwargs)

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

        def _call_it_back() -> None:
            """Internal method to repeatedly invoke the callback function at specified intervals. It uses the
            `pause.milliseconds()` method to handle the waiting periods between each invocation.
            """
            pause.milliseconds(interval_ms if delay_ms > 0 else 0)
            while self.alive:
                args = cb_fn_args if cb_fn_args else []
                xargs = cb_fn_kwargs if cb_fn_kwargs else {}
                callback(*args, **xargs)
                pause.milliseconds(interval_ms)

        self._add(f"Every-{callback.__name__}", _call_it_back)

    def _add(self, thread_name: str, callback: Callable, *args, **kwargs) -> None:
        """TODO"""
        th_new: Thread = Thread(name=thread_name, target=callback, args=args, kwargs=kwargs)
        self._not_started.append(th_new)
        self._threads[thread_name] = th_new

    def _remove(self, not_started: Thread) -> None:
        """TODO"""
        self._not_started.remove(not_started)


assert (scheduler := Scheduler().INSTANCE) is not None
