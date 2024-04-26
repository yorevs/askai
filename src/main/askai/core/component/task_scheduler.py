import logging as log
import re
import signal
import threading
from datetime import datetime, timedelta
from threading import Timer, Thread
from typing import Callable, Any, Iterable, Mapping

import pause
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_argument


class Scheduled:
    """TODO"""

    @staticmethod
    def every(interval_ms: int, delay_ms: int):
        """TODO"""
        def every_wrapper(func: Callable, *fargs, **fkwargs):
            scheduler.set_interval(interval_ms, func, delay_ms, *fargs, **fkwargs)
            return None

        return every_wrapper

    @staticmethod
    def at(hour: int, minute: int, second: int, millis: int):
        """TODO"""
        def at_wrapper(func: Callable, *fargs, **fkwargs):
            scheduler.schedule(hour, minute, second, millis, func, *fargs, **fkwargs)
            return None
        return at_wrapper


class TaskScheduler(Thread, metaclass=Singleton):
    """TODO"""

    INSTANCE: 'TaskScheduler'

    _done = False

    def __init__(self):
        super().__init__()
        self._today = datetime.today()
        self._threads: list[Thread] = []
        self._timers: list[Timer] = []
        signal.signal(signal.SIGINT, TaskScheduler._interrupt_handler)

    def run(self) -> None:
        while not self._done and threading.main_thread().is_alive():
            pause.milliseconds(200)

    def start(self) -> None:
        if not self.is_alive():
            super().start()
            list(map(lambda tmr: tmr.start(), self._timers))
            list(map(lambda th: th.start(), self._threads))

    @staticmethod
    def _interrupt_handler(*args) -> None:
        TaskScheduler._done = True
        log.warning("Scheduler interrupted: '%s'", str(args))

    def schedule(
        self,
        hh: int, mm: int, ss: int, us: int,
        cb_function: Callable,
        cf_fn_args: Iterable | None = None,
        cf_fn_kwargs: Mapping[str, Any] | None = None
    ) -> None:
        """TODO"""

        run_at: datetime = self._today.replace(
            day=self._today.day, hour=hh, minute=mm, second=ss, microsecond=us)
        delta_t: timedelta = run_at - self._today
        check_argument(delta_t.total_seconds() > 0, ">> Time is in the past <<")
        secs: float = max(0, delta_t.seconds) + 1
        print("Task", cb_function.__qualname__, " has been scheduled to", run_at)
        self._timers.append(Timer(secs, cb_function, *(cf_fn_args or []), **(cf_fn_kwargs or {})))

    def schedule_at(
        self,
        when: str,
        cb_function: Callable,
        cf_fn_args: Iterable | None = None,
        cf_fn_kwargs: Mapping[str, Any] | None = None) -> None:
        """TODO"""

        when_parts: list[int] = list(map(int, re.split(r'[:,;|]', when)))
        check_argument(len(when_parts) == 4)

        self.schedule(
            when_parts[0], when_parts[1], when_parts[2], when_parts[3], cb_function, cf_fn_args, cf_fn_kwargs)

    def set_interval(
        self,
        interval_ms: int,
        callback: Callable,
        delay_ms: int = 0,
        *cf_fn_args: Iterable | None,
        **cf_fn_kwargs: Iterable | None
    ) -> None:
        """TODO"""

        def __task__():
            if delay_ms > 0:
                pause.milliseconds(interval_ms)
            while not self._done:
                callback(*cf_fn_args, **cf_fn_kwargs)
                pause.milliseconds(interval_ms)

        self._threads.append(Thread(target=__task__))


assert (scheduler := TaskScheduler().INSTANCE) is not None
