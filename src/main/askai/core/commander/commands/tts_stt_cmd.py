#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.tts_stt_cmd
      @file: tts_stt_cmd.py
   @created: Thu, 25 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
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


class TtsSttCmd(ABC):
    """TODO"""

    @staticmethod
    def voice_list() -> None:
        """TODO"""
        all_voices = shared.engine.voices()
        str_voices = '\n'.join([f"{i}. {v.title()}" for i, v in enumerate(all_voices)])
        text_formatter.cmd_print(
            f"Available `{shared.engine.configs.stt_model}` voices: \n"
            f"\n{str_voices}\n> Hint: Type: '/voices set \\<number|voice_name\\>' to select a voice. "
            f"To hear a sample use: '/voices play \\<number|voice_name\\>'"
        )

    @staticmethod
    def voice_set(name: str | int | None = None) -> None:
        """TODO"""
        all_voices = shared.engine.voices()
        if name.isdecimal() and 0 <= int(name) <= len(all_voices):
            name = all_voices[int(name)]
        if name in all_voices:
            settings.put("openai.text.to.speech.voice", name)
            shared.engine.configs.tts_voice = name
            text_formatter.cmd_print(f"`Speech-To-Text` voice changed to %GREEN%{name.title()}%NC%")
        else:
            text_formatter.cmd_print(f"%RED%Invalid voice: '{name}'%NC%")

    @staticmethod
    def voice_play(name: str | int | None = None) -> None:
        """TODO"""
        all_voices = shared.engine.voices()
        ai_name = shared.engine.ai_name().lower().replace('engine', '')
        if name.isdecimal() and 0 <= int(name) <= len(all_voices):
            name = all_voices[int(name)]
        if name in all_voices:
            text_formatter.cmd_print(f"Sampling voice `{name}` …")
            player.play_sfx(f"voices/{ai_name}-{name}-sample")
        else:
            text_formatter.cmd_print(f"%RED%Invalid voice: '{name}'%NC%")

    @staticmethod
    def tempo(speed: int | None = None) -> None:
        """TODO"""
        if not speed:
            settings.get("askai.text.to.speech.tempo")
        elif 1 <= speed <= 3:
            settings.put("askai.text.to.speech.tempo", speed)
            configs.tempo = speed
            tempo_str: str = 'Normal' if speed == 1 else ('Fast' if speed == 2 else 'Ultra')
            text_formatter.cmd_print(f"`Speech-To-Text` **tempo** changed to %GREEN%{tempo_str} ({speed})%NC%")
        else:
            text_formatter.cmd_print(f"%RED%Invalid tempo value: '{speed}'. Please choose between [1..3].%NC%")

    @staticmethod
    def device_list() -> None:
        """TODO"""
        all_devices = recorder.devices
        str_voices = '\n'.join([f"{d[0]}. {d[1]}" for d in all_devices])
        text_formatter.cmd_print(
            f"Available audio input devices: \n"
            f"\n{str_voices}\n> Hint: Type: '/devices set \\<number\\>' to select a device."
        )

    @staticmethod
    def device_set(name: str | int | None = None) -> None:
        """TODO"""
        all_devices = recorder.devices
        if name.isdecimal() and 0 <= int(name) <= len(all_devices):
            name = all_devices[int(name)][1]
        if device := next((dev for dev in all_devices if dev[1] == name), None):
            if recorder.test_device(device[0]):
                recorder._input_device = device[0]
                configs.add_device(device[1])
                text_formatter.cmd_print(f"`Text-To-Speech` device changed to %GREEN%{device[1]}%NC%")
            else:
                text_formatter.cmd_print(f"%RED%Device: '{name}' failed to initialize!%NC%")
        else:
            text_formatter.cmd_print(f"%RED%Invalid audio input device: '{name}'%NC%")
