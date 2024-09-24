#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: demo.components
      @file: scheduler.py
   @created: Tue, 23 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from threading import Timer

import pause
from askai.core.askai_cli import AskAiCli
from askai.core.component.audio_player import AudioPlayer
from askai.core.support.shared_instances import shared
from clitt.core.term.terminal import Terminal
from hspylib.core.tools.commons import sysout
from hspylib.core.tools.dict_tools import get_or_default

today = datetime.today()
th_dir: str = f"{Path.home()}/TechWeek"
song_file: str = f"{th_dir}/highway-to-hell-fade.mp3"
welcome_file: str = f"{th_dir}/techweek-welcome.txt"

assert Path(th_dir).exists(), "TechWeek directory does not exist!"
assert Path(song_file).exists(), "TechWeek song file does not exist!"
assert Path(welcome_file).exists(), "TechWeek welcome file does not exist!"

ppt_url: str = (
    "https://docs.google.com/presentation/d/"
    "1oIoDNZHIxRL0_xEsKn7oC1fe8tcd18dDB3uQXrOnbSI/edit#slide=id.g5c786f5260_0_18"
)

hh: int = int(get_or_default(sys.argv, 1, today.hour))
mm: int = int(get_or_default(sys.argv, 2, today.minute))
ss: int = int(get_or_default(sys.argv, 3, today.second + 30))

t1: Timer | None = None
t2: Timer | None = None

done: bool = False

intro: str = """
 ___       _                 _            _
|_ _|_ __ | |_ _ __ ___   __| |_   _  ___(_)_ __   __ _
 | || '_ \\| __| '__/ _ \\ / _` | | | |/ __| | '_ \\ / _` |
 | || | | | |_| | | (_) | (_| | |_| | (__| | | | | (_| |
|___|_| |_|\\__|_|  \\___/ \\__,_|\\__,_|\\___|_|_| |_|\\__, |
                                                  |___/
 _____     _
|_   _|_ _(_)_   _ ___
  | |/ _` | | | | / __|
  | | (_| | | |_| \\__ \\
  |_|\\__,_|_|\\__,_|___/
"""


def taius_intro() -> None:
    global done
    with open(welcome_file) as f_pt:
        Terminal.clear()
        sysout(f"%GREEN%{intro}%NC%")
        ai = AskAiCli(False, False, False, False, 1, "taius", "openai", "gpt-3.5-turbo", f_pt.readlines())
        ai.run()
        pause.seconds(1)
        Terminal.shell_exec(f"open {ppt_url}")
        done = True


def play_intro() -> None:
    pause.seconds(3)
    sysout(f"%GREEN%{shared.nickname}: %RED%🎸🤘 LET'S ROCK !!! 🤘🎸%NC% ")
    AudioPlayer.play_audio_file(song_file)


if __name__ == "__main__":
    y: datetime = today.replace(day=today.day, hour=hh, minute=mm, second=ss, microsecond=0)
    delta_t: timedelta = y - today
    secs: float = max(0, delta_t.seconds) + 1

    t1 = Timer(secs, taius_intro).start()
    t2 = Timer(secs, play_intro).start()
    Terminal.clear()
    count = secs

    while not done:
        if count > 0:
            sysout(f"%GRAY%%HOM%%EL2%{count}%NC%", end="")
            count -= 1
        pause.seconds(1)
