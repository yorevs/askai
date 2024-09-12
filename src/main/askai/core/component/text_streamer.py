from askai.core.support.presets import Presets
from askai.core.support.text_formatter import text_formatter
from askai.language.language import Language
from clitt.core.term.commons import Direction
from clitt.core.term.cursor import cursor
from hspylib.core.metaclass.singleton import Singleton
from hspylib.modules.cli.keyboard import Keyboard
from hspylib.modules.cli.vt100.vt_color import VtColor
from threading import Thread
from typing import AnyStr

import os
import pause
import sys


class TextStreamer(metaclass=Singleton):
    """Provide a TypeWriter effect helper. This class can sync spoken language with streamed text."""

    INSTANCE: "TextStreamer"

    DONE: bool = False

    STREAMING: bool = False

    STREAMER_THREAD: Thread = None

    @staticmethod
    def _process(text: AnyStr, prefix: AnyStr = "", tempo: int = 1, language: Language = Language.EN_US) -> None:
        """Stream the text on the screen with a typewriter effect. This method simulates the effect of text being typed
        out character by character, with the speed of the effect determined by the tempo parameter. The effect can be
        customized based on the selected language.
        :param text: The text to be streamed.
        :param prefix: A prefix to prepend to the streaming text (optional).
        :param tempo: The speed multiplier for the typewriter effect (default is 1).
        :param language: The language used to stream the text (default is Language.EN_US).
        """
        presets: Presets = Presets.get(language.language, tempo=tempo)
        word_count: int = 0
        ln: str = os.linesep
        hide: bool = False
        idx: int = 0
        TextStreamer.STREAMING = True
        TextStreamer.DONE = False

        # The following algorithm was created based on the OpenAI 'whisper' speech.
        cursor.save()
        cursor.write(f"{str(prefix)}", end="")
        for i, char in enumerate(str(text)):
            if Keyboard.kbhit():
                sys.stdin.read(1)
                break
            if char == "%" and (i + 1) < len(text):
                try:
                    if (color := text[i + 1 : text.index("%", i + 1)]) in VtColor.names():
                        hide, idx = True, text.index("%", i + 1)
                        cursor.write(f"%{color}%", end="")
                        continue
                except ValueError:
                    pass  # this means that this '%' is not a VtColor specification
            if hide and idx is not None and i <= idx:
                continue
            cursor.write(char, end="")
            if char.isalpha():
                pause.seconds(presets.base_speed)
            elif char.isnumeric():
                pause.seconds(
                    presets.breath_interval if i + 1 < len(text) and text[i + 1] == "." else presets.number_interval
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
                    presets.base_speed if i + 1 < len(text) and text[i + 1].isnumeric() else presets.punct_interval
                )
            elif char == ln:
                pause.seconds(
                    presets.period_interval if i + 1 < len(text) and text[i + 1] == ln else presets.punct_interval
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
        cursor.restore()
        cursor.erase(Direction.DOWN)
        cursor.write(f"{str(prefix)}{text_formatter.beautify(text)}", markdown=True)
        TextStreamer.STREAMING = False
        TextStreamer.DONE = True

    def stream_text(
        self, text: AnyStr, prefix: AnyStr = "", tempo: int = 1, language: Language = Language.EN_US
    ) -> None:
        """TODO"""
        TextStreamer.STREAMER_THREAD = Thread(daemon=True, target=self._process, args=(text, prefix, tempo, language))
        TextStreamer.STREAMER_THREAD.start()
        TextStreamer.STREAMER_THREAD.join()


assert (streamer := TextStreamer().INSTANCE) is not None
