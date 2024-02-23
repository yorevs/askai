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
from clitt.core.term.cursor import Cursor
from clitt.core.term.screen import Screen
from clitt.core.term.terminal import Terminal
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.enums.charset import Charset
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import is_debugging
from hspylib.modules.cli.vt100.vt_color import VtColor
from hspylib.modules.eventbus.event import Event
from hspylib.modules.eventbus.eventbus import subscribe

from askai.__classpath__ import _Classpath
from askai.core.askai_events import AskAiEvents
from askai.core.components.stream_capturer import StreamCapturer
from askai.language.language import Language
from askai.utils.constants import Constants
from askai.utils.presets import Presets


class Display(metaclass=Singleton):
    """Provide an interface to display text on the screen."""

    INSTANCE = None

    SPLASH = _Classpath.get_resource_path("splash.txt").read_text(encoding=Charset.UTF_8.val)

    _BUFFER = []

    _STREAM = []

    def __init__(self):
        self._done: bool = False
        self._screen: Screen = Screen.INSTANCE
        self._streaming: bool = False
        self._display_thread: Thread = Thread(
            daemon=True, target=self._run
        )
        self._display_thread.start()
        self._capturer = StreamCapturer().start()

    @property
    def screen(self) -> Screen:
        return self._screen

    @property
    def cursor(self) -> Cursor:
        return self.screen.cursor

    def join(self) -> None:
        self._display_thread.join()

    def _terminate(self) -> None:
        self._done = True

    def _run(self) -> None:
        """TODO"""
        if not is_debugging():
            Terminal.alternate_screen(True)
        self._splash()
        while not self._done:
            while self._streaming:
                pause.milliseconds(100)
            if self._BUFFER and (next_text := self._BUFFER.pop()):
                self._display(next_text['text'], next_text['end'], next_text['erase_last'])
            elif self._STREAM and (next_stream := self._STREAM.pop()):
                self._stream(next_stream['text'], next_stream['tempo'], next_stream['lang'])
            else:
                pause.milliseconds(100)
        if not is_debugging():
            pause.seconds(1)  # Wait a bit before switching the screen back.
            Terminal.alternate_screen(False)

    def _splash(self) -> None:
        self.cursor.write(f"%GREEN%{self.SPLASH}%NC%")
        while not self._BUFFER and not self._STREAM:
            pause.milliseconds(100)
        pause.seconds(1)
        self.screen.clear()

    @staticmethod
    @subscribe(bus=Constants.DISPLAY_BUS, event=Constants.DISPLAY_EVENT)
    def _buffer_insert(ev: Event) -> None:
        """Insert a text in the display buffer to be displayed.
        :param ev: the display event.
        """
        Display._BUFFER.insert(0, {"text": ev.args.text, "end": ev.args.end, "erase_last": ev.args.erase_last})

    @staticmethod
    @subscribe(bus=Constants.DISPLAY_BUS, event=Constants.STREAM_EVENT)
    def _stream_insert(ev: Event) -> None:
        """Insert a text in the stream buffer to be streamed.
        :param ev: the stream event.
        """
        Display._STREAM.insert(0, {"text": ev.args.text, "tempo": ev.args.tempo, "lang": ev.args.lang})

    def _display(self, text: str, end: str = os.linesep, erase_last: bool = False) -> None:
        """Write the text on the screen."""
        if erase_last:
            self.cursor.erase_line()
        self.cursor.write(text, end=end)

    def _stream(
        self,
        text: str,
        tempo: int = 1,
        language: Language = Language.EN_US
    ) -> None:
        """Stream the text on the screen. Simulates a typewriter effect. The following presets were
        benchmarked according to the selected language.
        :param text: the text to stream.
        :param tempo: the speed multiplier of the typewriter effect. Defaults to 1.
        :param language: the language used to stream the text. Defaults to en_US.
        """
        self._streaming = True
        text: str = VtColor.strip_colors(text)
        presets: Presets = Presets.get(language.language, tempo=tempo)
        word_count: int = 0
        ln: str = os.linesep

        # The following algorithm was created based on the whisper voice.
        for i, char in enumerate(text):
            self.cursor.write(char, end="")
            if char.isalpha():
                pause.seconds(presets.base_speed)
            elif char.isnumeric():
                pause.seconds(
                    presets.breath_interval
                    if i + 1 < len(text) and text[i + 1] == "."
                    else presets.number_interval
                )
            elif char.isspace():
                if i - 1 >= 0 and not text[i - 1].isspace():
                    word_count += 1
                    pause.seconds(
                        presets.breath_interval
                        if word_count % presets.words_per_breath == 0
                        else presets.words_interval
                    )
                elif i - 1 >= 0 and not text[i - 1] in [".", "?", "!"]:
                    word_count += 1
                    pause.seconds(
                        presets.period_interval
                        if word_count % presets.words_per_breath == 0
                        else presets.punct_interval
                    )
            elif char == "/":
                pause.seconds(
                    presets.base_speed
                    if i + 1 < len(text) and text[i + 1].isnumeric()
                    else presets.punct_interval
                )
            elif char == ln:
                pause.seconds(
                    presets.period_interval
                    if i + 1 < len(text) and text[i + 1] == ln
                    else presets.punct_interval
                )
                word_count = 0
            elif char in [":", "-"]:
                pause.seconds(
                    presets.enum_interval
                    if i + 1 < len(text) and (text[i + 1].isnumeric() or text[i + 1] in [" ", ln, "-"])
                    else presets.base_speed
                )
            elif char in [",", ";"]:
                pause.seconds(
                    presets.comma_interval if i + 1 < len(text) and text[i + 1].isspace() else presets.base_speed
                )
            elif char in [".", "?", "!", ln]:
                pause.seconds(presets.punct_interval)
                word_count = 0
            pause.seconds(presets.base_speed)
        self.cursor.writeln("")
        self._streaming = False


assert Display().INSTANCE is not None

if __name__ == '__main__':
    d = Display.INSTANCE
    AskAiEvents.DISPLAY_BUS.events.display.emit(text="Processing, please wait...")
    pause.seconds(1)
    AskAiEvents.DISPLAY_BUS.events.display.emit(text="Second displayed text!!!", erase_last=True)
    AskAiEvents.DISPLAY_BUS.events.stream.emit(text="Text to be streamed!!!")
    AskAiEvents.DISPLAY_BUS.events.stream.emit(text="Second text to be streamed!!!")
    pause.seconds(5)
    line_input("Terminate ??? ")
    # print("AQUI")
    # AskAiEvents.DISPLAY_BUS.events.terminate.emit()
    d.join()
