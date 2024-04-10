#!/usr/bin/env python3

import os
import sys
from datetime import datetime
from threading import Timer

from clitt.core.term.terminal import Terminal
from hspylib.core.tools.commons import sysout
from hspylib.core.tools.dict_tools import get_or_default

from askai.core.askai import AskAi
from askai.core.component.audio_player import AudioPlayer

today = datetime.today()

th_dir: str = f'{os.getenv("HOME")}/Desktop/TechWeek'
ppt: str = (
    'https://docs.google.com/presentation/d/'
    '1oIoDNZHIxRL0_xEsKn7oC1fe8tcd18dDB3uQXrOnbSI/edit#slide=id.g5c786f5260_0_18')

hh = int(get_or_default(sys.argv, 1, '23'))
mm = int(get_or_default(sys.argv, 2, '30'))
ss = int(get_or_default(sys.argv, 3, '00'))

ss_diff = 2

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


def play_intro():
    def _exec_():
        song_file = f"{th_dir}/highway-to-hell-fade.mp3"
        AudioPlayer.play_audio_file(song_file)
    y = today.replace(day=today.day, hour=hh, minute=mm, second=(ss + ss_diff), microsecond=0)
    delta_t = y - today
    secs = delta_t.seconds + 1
    Timer(secs, _exec_).start()


def taius_intro():
    def _exec_():
        Terminal.clear()
        sysout(f"%GREEN%{intro}%NC%")
        play_intro()
        with open(f"{th_dir}/techweek-welcome.txt") as f_pt:
            ai = AskAi(
                False, False, False, 1,
                'taius-prompt', 'openai', 'gpt-3.5-turbo',
                f_pt.readlines())
            ai.run()
            Terminal.shell_exec(f'open {ppt}')
    y = today.replace(day=today.day, hour=hh, minute=mm, second=ss, microsecond=0)
    delta_t = y - today
    secs = delta_t.seconds + 1
    Timer(secs, _exec_).start()


if __name__ == '__main__':
    taius_intro()
