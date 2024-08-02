#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.tts_stt_cmd
      @file: tts_stt_cmd.py
   @created: Thu, 25 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from abc import ABC
from askai.core.askai_configs import configs
from askai.core.askai_settings import settings
from askai.core.component.audio_player import player
from askai.core.component.recorder import recorder
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import copy_file
from pathlib import Path

import os


class TtsSttCmd(ABC):
    """Provides Speech-to-Text (STT) and Text-to-Speech (TTS) command functionalities."""

    @staticmethod
    def voice_list() -> None:
        """List all available voices for the current engine/model."""
        all_voices = shared.engine.voices()
        str_voices = "\n".join([f"{i}. {v.title()}" for i, v in enumerate(all_voices)])
        text_formatter.cmd_print(
            f"Available `{shared.engine.configs().stt_model}` voices: \n"
            f"\n{str_voices}\n> Hint: Type: '/voices set \\<number|voice_name\\>' to select a voice. "
            f"To hear a sample use: '/voices play \\<number|voice_name\\>'"
        )

    @staticmethod
    def voice_set(name: str | int | None = None) -> None:
        """Set the specified engine's voice."""
        all_voices = shared.engine.voices()
        if name.isdecimal() and 0 <= int(name) <= len(all_voices):
            name = all_voices[int(name)]
        if name in all_voices:
            settings.put("openai.text.to.speech.voice", name)
            shared.engine.configs().tts_voice = name
            text_formatter.cmd_print(f"`Speech-To-Text` voice changed to %GREEN%{name.title()}%NC%")
        else:
            text_formatter.cmd_print(f"%RED%Invalid voice: '{name}'%NC%")

    @staticmethod
    def voice_play(name: str | int | None = None) -> None:
        """Play a sample using the specified voice."""
        all_voices = shared.engine.voices()
        ai_name = shared.engine.ai_name().lower().replace("engine", "")
        if name.isdecimal() and 0 <= int(name) <= len(all_voices):
            name = all_voices[int(name)]
        if name in all_voices:
            text_formatter.cmd_print(f"Sampling voice `{name}` …")
            player.play_sfx(f"voices/{ai_name}-{name}-sample")
        else:
            text_formatter.cmd_print(f"%RED%Invalid voice: '{name}'%NC%")

    @staticmethod
    def tempo(speed: int | None = None) -> None:
        """Set the playing speed of the speech."""
        if not speed:
            settings.get("askai.text.to.speech.tempo")
        elif 1 <= speed <= 3:
            settings.put("askai.text.to.speech.tempo", speed)
            configs.tempo = speed
            tempo_str: str = "Normal" if speed == 1 else ("Fast" if speed == 2 else "Ultra")
            text_formatter.cmd_print(f"`Speech-To-Text` **tempo** changed to %GREEN%{tempo_str} ({speed})%NC%")
        else:
            text_formatter.cmd_print(f"%RED%Invalid tempo value: '{speed}'. Please choose between [1..3].%NC%")

    @staticmethod
    def device_list() -> None:
        """List the available audio input devices."""
        all_devices = recorder.devices
        str_devices = "\n".join([f"{d[0]}. {d[1]}" for d in all_devices])
        text_formatter.cmd_print(
            f"Current audio input device: {recorder.input_device} \n"
            f"\nAvailable audio input devices: \n"
            f"\n{str_devices}\n> Hint: Type: '/devices set \\<number\\>' to select a device."
        )

    @staticmethod
    def device_set(name: str | int | None = None) -> None:
        """Set the current audio input device."""
        all_devices = recorder.devices
        if name.isdecimal() and 0 <= int(name) <= len(all_devices):
            name = all_devices[int(name)][1]
        if device := next((dev for dev in all_devices if dev[1] == name), None):
            if recorder.set_device(device):
                text_formatter.cmd_print(f"`Text-To-Speech` device changed to %GREEN%{device[1]}%NC%")
            else:
                text_formatter.cmd_print(f"%RED%Device: '{name}' failed to initialize!%NC%")
        else:
            text_formatter.cmd_print(f"%RED%Invalid audio input device: '{name}'%NC%")

    @staticmethod
    def tts(text: str, dest_dir: str = os.getcwd(), playback: bool = True) -> None:
        """Convert a text to speech."""
        if (audio_path := shared.engine.text_to_speech(text, stream=False, playback=playback)) and audio_path.exists():
            if dest_dir and ((dest_path := Path(dest_dir)) and dest_path.exists()):
                audio_path = copy_file(audio_path, dest_dir)
            text_formatter.cmd_print(f"File %GREEN%'{audio_path}' was successfully saved!%NC%")
        else:
            text_formatter.cmd_print(f"%RED%Unable to convert text to file !%NC%")
