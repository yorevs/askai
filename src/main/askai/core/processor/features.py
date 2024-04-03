import inspect
import logging as log
import os
import re
import sys
from functools import lru_cache
from typing import Optional

from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import sysout

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.processor.tools.analysis import check_output
from askai.core.processor.tools.browser import browse
from askai.core.processor.tools.general import fetch, display
from askai.core.processor.tools.summarization import summarize
from askai.core.processor.tools.terminal import execute_command, list_contents


class Features(metaclass=Singleton):
    """TODO"""

    INSTANCE: 'Features' = None

    RESERVED: list[str] = ['invoke', 'list_features']

    def __init__(self):
        self._all = dict(filter(
            lambda pair: pair[0] not in self.RESERVED and not pair[0].startswith('_'), {
                n: fn for n, fn in inspect.getmembers(self, predicate=inspect.ismethod)
            }.items()))

    @lru_cache
    def invoke(self, action: str, context: str = '') -> Optional[str]:
        """TODO"""
        re_fn = r'([a-zA-Z]\w+)\s*\((.*)\)'
        if act_fn := re.findall(re_fn, action):
            fn = self._all[act_fn[0][0]]
            args: list[str] = re.sub("['\"]", '', act_fn[0][1]).split(',')
            args.append(context)
            return fn(*list(map(str.strip, args)))
        return None

    @lru_cache
    def enlist(self) -> str:
        doc_strings: str = ''
        for fn in self._all.values():
            doc_strings += f"{fn.__doc__}{os.linesep}" if fn and fn.__doc__ else ''
        return doc_strings

    @lru_cache
    def _human_approval(self) -> bool:
        """Prompt for human approval. This is mostly used to execute terminal commands."""
        confirm_msg = (msg.access_grant())
        if (resp := line_input(confirm_msg).lower()) not in ("yes", "y"):
            raise ValueError(f"Terminal command execution no approved '{resp}' !")
        self._approved = True

        return self._approved

    def intelligible(self, *args: str) -> None:
        """'Intelligible question' -> Command = intelligible(question)"""
        AskAiEvents.ASKAI_BUS.events.reply_error.emit(message=msg.intelligible(args[0]))

    def terminate(self, *args: str) -> None:
        """'Terminate intent' -> Command = terminate(reason)"""
        log.info(f"Application exit: '%s'", args[0])
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.goodbye())
        sysout("")
        sys.exit(0)

    def impossible(self, *args: str) -> None:
        """'Impossible plan' -> Command = impossible(reason)"""
        AskAiEvents.ASKAI_BUS.events.reply_error.emit(message=msg.impossible(args[0]))

    def terminal(self, *args: str) -> str:
        """'Terminal command execution' -> Command = terminal(shell, command)"""
        return execute_command(args[0], args[1])

    def list_contents(self, *args: str) -> str:
        """'List folder contents' -> Command = list_contents(folder)"""
        return list_contents(args[0])

    def check_output(self, *args: str) -> str:
        """'Check output' -> Command = check_output(question)"""
        return check_output(args[0], args[1])

    def summarize_files(self, *args: str) -> str:
        """'Summarization of files and folders' -> Command = summarize_files(folder, glob)"""
        return summarize(args[0], args[1])

    def browse(self, *args: str) -> str:
        """'Internet browsing' -> Command = browse(query)"""
        return browse(args[0])

    def describe_image(self, *args: str) -> str:
        """'Image analysis' -> Command = describe_image(image_path)"""
        raise NotImplementedError('This feature is not yet implemented !')

    def fetch(self, *args: str) -> str:
        """'Fetch from AI database' -> Command = fetch(query)"""
        return fetch(args[0])

    def display(self, *args: str) -> None:
        """'Display text' -> Command = display(text)"""
        display(' '.join(args))


assert (features := Features().INSTANCE) is not None
