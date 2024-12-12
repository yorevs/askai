from clitt.core.term.cursor import cursor
from clitt.core.term.terminal import Terminal
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.tools.commons import sysout, to_bool
from hspylib.modules.cli.vt100.vt_color import VtColor
from rich.console import Console
from threading import Thread

import contextlib
import itertools
import pause
import threading
import time


class Spinner(Enumeration):
    """TODO"""

    # fmt: off

    DEFAULT     = 200, ["●○○", "●●○", "●●●", "○●●", "○○●"]

    ARROW_BAR   = 220, ["▹▹▹", "▸▹▹", "▸▸▹", "▸▸▸"]

    BAR         = 50,  ["▁", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃"]

    BOUNCE      = 220, ['⠁', '⠂', '⠄', '⠂']

    BOX         = 220, ["▖", "▘", "▝", "▗"]

    BULLET      = 250, ["○", "●"]

    CIRCLE      = 220, ["◐", "◓", "◑", "◒"]

    COLIMA      = 70,  ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    HEXAGON     = 250, ["⬢", "⬡"]

    LINE_GROW   = 60,  ["    ", "=   ", "==  ", "=== ", " ===", "  ==", "   ="]

    LINE_BOUNCE = 60, ["    ", "=   ", "==  ", "=== ", "====", "=== ", "==  ", "=   "]

    STAR        = 180, ["✶", "✸", "✹", "✺", "✹", "✷"]

    # fmt: on

    def __init__(self, interval: int, symbols: list[str]):
        self._started: bool = False
        self._worker: Thread | None = None

    @property
    def started(self) -> bool:
        return self._started

    @started.setter
    def started(self, value: bool):
        self._started = to_bool(value)

    @contextlib.contextmanager
    def run(self, interval: int = None, prefix: str = None, suffix: str = None, color: VtColor = VtColor.WHITE) -> None:
        """TODO"""
        spinner = itertools.cycle(self.symbols)

        def _work_():
            try:
                Terminal.set_show_cursor(False)
                while threading.main_thread().is_alive():
                    pause.milliseconds(interval if interval else self.interval)
                    while not self.started and threading.main_thread().is_alive():
                        pause.milliseconds(interval if interval else self.interval)
                    cursor.write(color.placeholder)
                    smb: str = next(spinner)
                    cursor.write(f"{prefix + ' 'if prefix else ''}{smb}{' ' + suffix if suffix else ''}%NC%%ED0%")
                    cursor.restore()
            except InterruptedError:
                pass
            Terminal.set_show_cursor()

        self._worker = Thread(daemon=True, target=_work_)
        self._worker.start()
        yield self

    def start(self) -> None:
        """TODO"""
        self.started = True
        cursor.save()

    def stop(self) -> None:
        """TODO"""
        self.started = False
        sysout(f"%CUB({len(self.symbols[0])})%%EL0%", end="")

    def wait(self, timeout: int = None) -> None:
        """TODO"""
        self._worker.join(timeout)

    @property
    def interval(self) -> int:
        return self.value[0]

    @property
    def symbols(self) -> list[str]:
        return self.value[1]


if __name__ == "__main__":
    # Initialize the console
    console = Console()

    # Example usage of a spinner
    with console.status("[bold green]Working on tasks...", spinner="bouncingBar") as status:
        for i in range(3):
            time.sleep(2)  # Simulate work
            # Update the status to control spinner message
            status.update(f"[bold green]Task {i + 1}/3 in progress...")
            # Print task progress on a new line
            console.print(f"[bold green]√ Task {i + 1}/3 is done")
    console.print("[bold green] All tasks completed.")
