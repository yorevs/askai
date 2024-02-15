#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.utils
      @file: utilities.py
   @created: Wed, 10 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import hashlib
import logging as log
import os
import time
from functools import partial, lru_cache
from shutil import which
from typing import Callable

import pause
from clitt.core.term.terminal import Terminal
from hspylib.core.enums.charset import Charset
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import file_is_not_empty, sysout
from hspylib.core.tools.text_tools import ensure_endswith
from hspylib.modules.application.exit_status import ExitStatus
from hspylib.modules.cli.vt100.vt_color import VtColor
from speech_recognition import AudioData, Recognizer, Microphone, UnknownValueError, RequestError

from askai.__classpath__ import _Classpath
from askai.exception.exceptions import IntelligibleAudioError, InvalidRecognitionApiError, RecognitionApiRequestError
from askai.language.language import Language
from askai.utils.presets import Presets

# Sound effects directory.
SFX_DIR = str(_Classpath.resource_path()) + "/assets/sound-fx"

# AI Prompts directory.
PROMPT_DIR = str(_Classpath.resource_path()) + "/assets/prompts"


def hash_text(text: str) -> str:
    """Create a hash string based on the provided text.
    :param: text the text to be hashed.
    """
    return hashlib.md5(text.encode(Charset.UTF_8.val)).hexdigest()


@lru_cache
def calculate_delay_ms(audio_length_sec: float, text_length: int) -> float:
    """Calculate the required delay for one char to be printed according to the audio length in millis."""
    # Convert audio length from seconds to milliseconds
    audio_length_ms: float = audio_length_sec * 1000

    # Calculate characters per millisecond
    characters_per_ms: float = text_length * 1000 / audio_length_ms

    # Calculate delay in seconds for one character
    delay_sec = 1.0 / characters_per_ms

    return delay_sec * 1000


def stream(
    reply_str: str,
    tempo: int = 1,
    language: Language = Language.EN_US
) -> None:
    """Stream the response from the AI Engine. Simulates a typewriter effect. The following presets were
    benchmarked according to the selected speaker engine and language.
    :param reply_str: the text to stream.
    :param tempo: the speed multiplier of the typewriter effect. Defaults to 1.
    :param language: the language used to stream the text.
    """

    reply_str: str = VtColor.strip_colors(reply_str)
    presets: Presets = Presets.get(language.language, tempo=tempo)
    word_count: int = 0
    ln: str = os.linesep

    # The following algorithm was created based on the whisper voice.
    for i, char in enumerate(reply_str):
        sysout(char, end="")
        if char.isalpha():
            pause.seconds(presets.base_speed)
        elif char.isnumeric():
            pause.seconds(
                presets.breath_interval
                if i + 1 < len(reply_str) and reply_str[i + 1] == "."
                else presets.number_interval
            )
        elif char.isspace():
            if i - 1 >= 0 and not reply_str[i - 1].isspace():
                word_count += 1
                pause.seconds(
                    presets.breath_interval if word_count % presets.words_per_breath == 0 else presets.words_interval)
            elif i - 1 >= 0 and not reply_str[i - 1] in [".", "?", "!"]:
                word_count += 1
                pause.seconds(
                    presets.period_interval if word_count % presets.words_per_breath == 0 else presets.punct_interval)
        elif char == "/":
            pause.seconds(
                presets.base_speed
                if i + 1 < len(reply_str) and reply_str[i + 1].isnumeric()
                else presets.punct_interval
            )
        elif char == ln:
            pause.seconds(
                presets.period_interval
                if i + 1 < len(reply_str) and reply_str[i + 1] == ln
                else presets.punct_interval
            )
            word_count = 0
        elif char in [":", "-"]:
            pause.seconds(
                presets.enum_interval
                if i + 1 < len(reply_str) and (reply_str[i + 1].isnumeric() or reply_str[i + 1] in [" ", ln, "-"])
                else presets.base_speed
            )
        elif char in [",", ";"]:
            pause.seconds(
                presets.comma_interval if i + 1 < len(reply_str) and reply_str[i + 1].isspace() else presets.base_speed
            )
        elif char in [".", "?", "!", ln]:
            pause.seconds(presets.punct_interval)
            word_count = 0
        pause.seconds(presets.base_speed)
    sysout("")


def input_mic(
    fn_listening: partial,
    fn_processing: partial,
    fn_recognition: Callable[[AudioData], str]
) -> str:
    """Listen to the microphone and transcribe the speech into text.
    :param fn_listening: The function to display the listening message.
    :param fn_processing: The function to display the processing message.
    :param fn_recognition: The AI engine API to use to recognize the speech.
    """
    rec: Recognizer = Recognizer()
    with Microphone() as source:
        rec.adjust_for_ambient_noise(source, duration=1.5)
        fn_listening()
        audio: AudioData = rec.listen(source, timeout=5)
        Terminal.INSTANCE.cursor.erase_line()
        fn_processing()
        try:
            recognizer_api = getattr(rec, fn_recognition.__name__)
            if recognizer_api and isinstance(recognizer_api, Callable):
                return recognizer_api(audio).strip()
            raise InvalidRecognitionApiError(str(fn_recognition or "<none>"))
        except UnknownValueError as err:
            raise IntelligibleAudioError(str(err)) from err
        except RequestError as err:
            raise RecognitionApiRequestError(str(err))
        finally:
            Terminal.INSTANCE.cursor.erase_line()


@lru_cache
def start_delay() -> float:
    """Determine the amount of delay before start streaming the text."""
    log.debug("Determining the start delay")
    sample_duration_sec = 1.75  # We know the length
    started = time.time()
    play_sfx("sample.mp3")
    delay = max(0.0, time.time() - started - sample_duration_sec)
    log.debug("Detected a play delay of %s seconds", delay)

    return delay


@lru_cache
def audio_length(path_to_audio_file: str) -> float:
    check_argument(which("ffprobe") and file_is_not_empty(path_to_audio_file))
    ret: float = 0.0
    try:
        ret, code = Terminal.shell_exec(
            f'ffprobe -i {path_to_audio_file} -show_entries format=duration -v quiet -of csv="p=0"'
        )
        return float(ret) if code == ExitStatus.SUCCESS else 0.0
    except FileNotFoundError:
        log.error("Audio file was not found: %s !", path_to_audio_file)
    except TypeError:
        log.error("Could not determine audio duration !")

    return ret


def play_audio_file(path_to_audio_file: str, tempo: int = 1) -> bool:
    """Play the specified mp3 file using ffplay (ffmpeg) application.
    :param path_to_audio_file: the path to the mp3 file to be played.
    :param tempo: the playing speed.
    """
    check_argument(which("ffplay") and file_is_not_empty(path_to_audio_file))
    try:
        out, code = Terminal.shell_exec(
            f'ffplay -af "atempo={tempo}" -v 0 -nodisp -autoexit {path_to_audio_file}'
        )
        return code == ExitStatus.SUCCESS
    except FileNotFoundError:
        log.error("Audio file was not found: %s !", path_to_audio_file)

    return False


def play_sfx(filename: str) -> bool:
    """Play a sound effect audio file.
    :param filename: The filename of the sound effect.
    """
    filename = f"{SFX_DIR}/{ensure_endswith(filename, '.mp3')}"
    check_argument(file_is_not_empty(filename), f"Sound effects file does not exist: {filename}")

    return play_audio_file(filename)


@lru_cache
def read_prompt(filename: str) -> str:
    """Read the prompt specified by the filename.
    :param filename: The filename of the prompt.
    """
    filename = f"{PROMPT_DIR}/{ensure_endswith(filename, '.txt')}"
    check_argument(file_is_not_empty(filename), f"Prompt file does not exist: {filename}")
    with open(filename) as f_prompt:
        return "".join(f_prompt.readlines())
