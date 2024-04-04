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
from askai.core.proxy.tools.analysis import check_output, stt
from askai.core.proxy.tools.browser import browse
from askai.core.proxy.tools.general import fetch, display
from askai.core.proxy.tools.summarization import summarize
from askai.core.proxy.tools.terminal import execute_command, list_contents


class Features(metaclass=Singleton):
    """This class provides the AskAI available features."""

    INSTANCE: 'Features' = None

    RESERVED: list[str] = ['invoke', 'list_features']

    def __init__(self):
        self._all = dict(filter(
            lambda pair: pair[0] not in self.RESERVED and not pair[0].startswith('_'), {
                n: fn for n, fn in inspect.getmembers(self, predicate=inspect.ismethod)
            }.items()))

    def invoke(self, action: str, context: str = '') -> Optional[str]:
        """Invoke the action with its arguments and context."""
        re_fn = r'([a-zA-Z]\w+)\s*\((.*)\)'
        if act_fn := re.findall(re_fn, action):
            fn_name = act_fn[0][0].lower()
            fn = self._all[fn_name]
            args: list[str] = re.sub("['\"]", '', act_fn[0][1]).split(',')
            args.append(context)
            return fn(*list(map(str.strip, args)))
        return None

    @lru_cache
    def enlist(self) -> str:
        """Return an 'os.linesep' separated string list of feature descriptions."""
        doc_strings: str = ''
        for fn in self._all.values():
            doc_strings += f"{fn.__doc__}{os.linesep}" if fn and fn.__doc__ else ''
        return doc_strings

    def _human_approval(self) -> bool:
        """Prompt for human approval. This is mostly used to execute terminal commands."""
        confirm_msg = (msg.access_grant())
        if (resp := line_input(confirm_msg).lower()) not in ("yes", "y"):
            raise ValueError(f"Terminal command execution no approved '{resp}' !")
        self._approved = True

        return self._approved

    def intelligible(self, *args: str) -> None:
        """Feature: 'Intelligible question', Usage: 'intelligible(<question>, <reason>)'"""
        AskAiEvents.ASKAI_BUS.events.reply_error.emit(message=msg.intelligible(args[0]))

    def terminate(self, *args: str) -> None:
        """Feature: 'Terminate intent', Usage: 'terminate(<reason>)'"""
        log.info(f"Application exit: '%s'", args[0])
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.goodbye())
        sysout("")
        sys.exit(0)

    def impossible(self, *args: str) -> None:
        """Feature: 'Impossible plan', Usage: 'impossible(<reason>)'"""
        AskAiEvents.ASKAI_BUS.events.reply_error.emit(message=msg.impossible(args[0]))

    def terminal(self, *args: str) -> str:
        """Feature: 'Terminal command execution', Usage: 'terminal(<shell>, <command>)'"""
        return execute_command(args[0], args[1])

    def list_contents(self, *args: str) -> str:
        """Feature: 'List folder contents', Usage: 'list_contents(<folder>)'"""
        return list_contents(args[0])

    def check_output(self, *args: str) -> str:
        """Feature: 'Check output', Usage: 'check_output(<question>)'"""
        return check_output(args[0], args[1])

    def summarize_files(self, *args: str) -> str:
        """Feature: 'Summarization of files and folders', Usage: 'summarize_files(<folder>, <glob>)'"""
        return summarize(args[0], args[1])

    def browse(self, *args: str) -> str:
        """Feature: 'Internet browsing', Usage: 'browse(<search_query>)'"""
        return browse(args[0])

    def describe_image(self, *args: str) -> str:
        """Feature: 'Image analysis', Usage: 'describe_image(<image_path>)'"""
        raise NotImplementedError('This feature is not yet implemented !')

    def fetch(self, *args: str) -> str:
        """Feature: 'AI database retrival', Usage: 'fetch(<query>)'"""
        return fetch(args[0])

    def display(self, *args: str) -> None:
        """Feature: 'Display plain text', Usage: 'display(<text>)'"""
        display(' '.join(args))

    def stt(self, *args: str) -> str:
        """Feature: 'Display using STT techniques', Usage: 'stt(<question>, <text>)'"""
        return stt(args[0], ' '.join(args[1:]))


assert (features := Features().INSTANCE) is not None
