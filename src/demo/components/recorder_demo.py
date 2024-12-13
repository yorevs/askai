# fmt: off
import os
from textwrap import dedent

from clitt.core.term.cursor import cursor
from clitt.core.tui.line_input.line_input import line_input

from askai.core.askai_messages import msg
from askai.core.component.recorder import recorder
from utils import init_context

MENU = dedent(f"""\
> Recorder Demo options

1. Text-To-Speech
2. Device list
3. Dictate

$ """)
# fmt: on


if __name__ == "__main__":
    init_context("camera-demo")
    recorder.setup()
    while opt := line_input(MENU, placeholder="Select an option"):
        cursor.write()
        match opt:
            case "1":
                cursor.write(msg.listening())
                audio_path, stt_text = recorder.listen()
                cursor.writeln(f"Audio path: {audio_path}")
                cursor.writeln(f"Transcribed text: {stt_text}")
            case "2":
                list(map(lambda d: cursor.write(str(d) + os.linesep), recorder.devices))
            case "3":
                dictated_text = recorder.dictate()
                cursor.writeln(f"\nDictated text: {dictated_text}")
            case _:
                continue
