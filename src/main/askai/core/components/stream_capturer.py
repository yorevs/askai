#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-Hqt
   @package: hqt
      @file: stream_capturer.py
   @created: Wed, 30 Jun 2021
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""

import io
import logging as log
from contextlib import redirect_stderr, redirect_stdout
from threading import Thread
from time import sleep

from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import is_debugging

from askai.core.askai_events import AskAiEvents


class StreamCapturer(Thread):
    """Thread to capture stdout and/or stderr messages and send them via EventBus."""

    class StdoutWorker(Thread):
        """Thread worker to capture stdout messages"""

        def __init__(self, parent: "StreamCapturer", poll_interval: float):
            super().__init__()
            self._poll_interval = poll_interval
            self._parent = parent

        def run(self):
            self.name = f"stdout-worker-{hash(self)}"
            with io.StringIO() as buf, redirect_stdout(buf):
                while self._parent.is_alive():
                    output = buf.getvalue()
                    if output and output != "":
                        log.debug("STDOUT captured => %s", output)
                        AskAiEvents.CAPTURER_BUS.events.stdoutCaptured.emit(output=output)
                        buf.truncate(0)
                    sleep(self._poll_interval)

    class StderrWorker(Thread):
        """Thread worker to capture stderr messages"""

        def __init__(self, parent: "StreamCapturer", poll_interval: float):
            super().__init__()
            self._poll_interval = poll_interval
            self._parent = parent

        def run(self):
            self.name = "stderr-worker-{hash(self)}"
            with io.StringIO() as buf, redirect_stderr(buf):
                while self._parent.is_alive():
                    output = buf.getvalue()
                    if output and output != "":
                        log.debug("STDERR captured => %s", output)
                        AskAiEvents.CAPTURER_BUS.events.stderrCaptured.emit(output=output)
                        buf.truncate(0)
                    sleep(self._poll_interval)

    def __init__(
        self,
        capture_stderr: bool = True,
        capture_stdout: bool = True,
        stdout_poll_interval: float = 0.5,
        stderr_poll_interval: float = 0.5,
    ):
        check_argument(capture_stderr or capture_stdout, "At least one capturer must be started")
        super().__init__()
        self.name = "stream-capturer"
        self._capture_stdout = capture_stdout
        self._capture_stderr = capture_stderr
        self._poll_interval = stdout_poll_interval + stderr_poll_interval

        if capture_stderr:
            self._stderr_capturer = self.StderrWorker(self, stderr_poll_interval)
        if capture_stdout:
            self._stdout_capturer = self.StdoutWorker(self, stdout_poll_interval)

    def run(self) -> None:
        if self._capture_stderr:
            self._stderr_capturer.start()
        if self._capture_stdout:
            self._stdout_capturer.start()
        while self.is_alive():
            sleep(self._poll_interval)

    def start(self) -> 'StreamCapturer':
        if not is_debugging():
            super().start()
        else:
            log.warning("Stderr/Stdout capture is not started in debugging mode")
        return self
