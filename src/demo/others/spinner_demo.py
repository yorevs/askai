import os

import pause
from askai.core.support.spinner import Spinner
from hspylib.core.tools.commons import sysout
from hspylib.modules.cli.vt100.vt_color import VtColor


def echo(message: str, prefix: str | None = None, end=os.linesep) -> None:
    """Prints a message with a prefix followed by the specified end character.
    :param message: The message to print.
    :param prefix: Optional prefix to prepend to the message.
    :param end: The string appended after the message (default is a newline character).
    """
    sysout(f"%CYAN%[{prefix[:22] if prefix else '':>23}]%NC%  {message:<80}" if not len(end) else message, end=end)


if __name__ == "__main__":
    # Example usage of the humanfriendly Spinner
    with Spinner.DEFAULT.run(suffix="Wait", color=VtColor.CYAN) as spinner:
        echo("Preparing the docs", "TASK", end="")
        spinner.start()
        pause.seconds(5)
        spinner.stop()
        echo("%GREEN%OK%NC%")
        echo("Running the jobs", "TASK", end="")
        spinner.start()
        pause.seconds(5)
        spinner.stop()
        echo("%GREEN%OK%NC%")
