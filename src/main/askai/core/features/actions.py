import inspect
import os
import re
from functools import lru_cache
from textwrap import dedent
from typing import Optional

from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.metaclass.singleton import Singleton

from askai.core.askai_messages import msg
from askai.core.features.tools.analysis import check_output, stt
from askai.core.features.tools.browser import browse
from askai.core.features.tools.general import fetch, display
from askai.core.features.tools.summarization import summarize
from askai.core.features.tools.terminal import execute_command, list_contents
from askai.exception.exceptions import ImpossibleQuery, UnintelligibleQuery, TerminatingQuery


class Actions(metaclass=Singleton):
    """This class provides the AskAI available actions."""

    INSTANCE: 'Actions' = None

    RESERVED: list[str] = ['invoke', 'enlist']

    def __init__(self):
        self._all = dict(filter(
            lambda pair: pair[0] not in self.RESERVED and not pair[0].startswith('_'), {
                n: fn for n, fn in inspect.getmembers(self, predicate=inspect.ismethod)
            }.items()))

    def invoke(self, question: str, action: str, context: str = '') -> Optional[str]:
        """Invoke the action with its arguments and context.
        :param question:
        :param action: The action to be performed.
        :param context: the action context.
        """
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
            doc_strings += f"{dedent(fn.__doc__.strip())}{os.linesep}" if fn and fn.__doc__ else ''
        return doc_strings

    def _human_approval(self) -> bool:
        """Prompt for human approval. This is mostly used to execute terminal commands."""
        confirm_msg = (msg.access_grant())
        if (resp := line_input(confirm_msg).lower()) not in ("yes", "y"):
            raise ValueError(f"Terminal command execution no appargs[0]roved '{resp}' !")
        self._approved = True

        return self._approved

    def unintelligible(self, *args: str) -> None:
        """
        Feature: 'Unintelligible question'
        Description: Useful when the question is unintelligible.
        Usage: 'unintelligible(<question>, <reason>)'
        """
        raise UnintelligibleQuery(f"{args[1]}: '{args[0]}'")

    def terminate(self, *args: str) -> None:
        """
        Feature: 'Terminating intention'
        Description: Useful when the user intends to end the conversation.
        Usage: 'terminate()'
        """
        raise TerminatingQuery('')

    def impossible(self, *args: str) -> None:
        """
        Feature: 'Impossible action or plan'
        Description: Useful when an action or plan is not possible to execute.
        Usage: 'impossible(<reason>)'
        """
        raise ImpossibleQuery(' '.join(args))

    def terminal(self, *args: str) -> str:
        """
        Feature: 'Terminal command execution'
        Description: Useful when you need to execute terminal commands.
        Usage: 'terminal(<term_type>, <command>)'
        """
        # TODO Check for permission before executing
        return execute_command(args[0], args[1])

    def list_contents(self, *args: str) -> str:
        """
        Feature: 'List folder contents'
        Description: Useful when you need to list folder contents.
        Usage: 'list_contents(<folder>)'
        """
        return list_contents(args[0])

    def check_output(self, *args: str) -> str:
        """
        Feature: 'Check output'
        Description: Useful when you introduce a command necessitating its output for subsequent actions.
        Usage: 'check_output(<question>)'
        """
        return check_output(args[0], args[1])

    def stt(self, *args: str) -> str:
        """
        Feature: 'Display using STT techniques'
        Description: Useful when you need to display the response using STT techniques.
        Usage: 'stt(<question>, <response>)'
        """
        return stt(args[0], args[1])

    def fetch(self, *args: str) -> str:
        """
        Feature: 'Time-independent database retrival'
        Description: Useful when you need to engage in casual conversations.
        Usage: 'fetch(<question>)'"""
        return fetch(args[0])

    def browse(self, *args: str) -> str:
        """
        Feature: 'Internet browsing'
        Description: Useful when you need to answer questions about current events.
        Usage: 'browse(<search_query>)'
        """
        return browse(args[0])

    def display(self, *args: str) -> str:
        """
        Feature: 'Display plain text'
        Description: Useful when you need to display any text.
        Usage: 'display(<text>, <text>, ...)'
        """
        return display(*args[:-1])

    def summarize_files(self, *args: str) -> str:
        """
        Feature: 'Summarization of files and folders'
        Description: Useful when you need to summarize files and folders.
        Usage: 'summarize_files(<folder>, <glob>)'
        """
        return summarize(args[0], args[1])

    def describe_image(self, *args: str) -> str:
        """
        Feature: 'Image analysis'
        Description: Useful when you need to describe an image.
        Usage: 'describe_image(<image_path>)'"""
        return str(NotImplementedError('This feature is not yet implemented !'))


assert (features := Actions().INSTANCE) is not None
