import inspect
import re
from functools import lru_cache
from textwrap import dedent
from typing import Optional

from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.metaclass.singleton import Singleton

from askai.core.askai_messages import msg
from askai.core.features.tools.analysis import check_output
from askai.core.features.tools.browser import browse
from askai.core.features.tools.general import fetch, display
from askai.core.features.tools.summarization import summarize
from askai.core.features.tools.terminal import execute_command, list_contents, open_command
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

    def invoke(self, action: str, context: str = '') -> Optional[str]:
        """Invoke the action with its arguments and context.
        :param action: The action to be performed.
        :param context: the action context.
        """
        re_fn = r'([a-zA-Z]\w+)\s*\((.*)\)'
        fn_name = None
        try:
            if act_fn := re.findall(re_fn, action):
                fn_name = act_fn[0][0].lower()
                fn = self._all[fn_name]
                args: list[str] = re.sub("['\"]", '', act_fn[0][1]).split(',')
                args.append(context)
                return fn(*list(map(str.strip, args)))
        except KeyError as err:
            raise ImpossibleQuery(f"Command not found: {fn_name} => {str(err)}")

        return None

    @lru_cache
    def enlist(self) -> str:
        """Return an 'os.linesep' separated string list of feature descriptions."""
        doc_strings: str = ''
        for fn in self._all.values():
            doc_strings += f"{dedent(fn.__doc__)}\n{'-' * 18}\n" if fn and fn.__doc__ else ''
        return doc_strings

    def _human_approval(self) -> bool:
        """Prompt for human approval. This is mostly used to execute terminal commands."""
        confirm_msg = (msg.access_grant())
        if (resp := line_input(confirm_msg).lower()) not in ("yes", "y"):
            raise ValueError(f"Terminal command execution was not approved '{resp}' !")
        self._approved = True

        return self._approved

    def unintelligible(self, *args: str) -> None:
        """
        Feature: 'Unintelligible question'
        Description: Useful when the question is unintelligible.
        Usage: 'unintelligible(<question>, <reason>)'
        - param <question>: The user question.
        - param <reason>: The reason why the question was not unintelligible.
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
        - param <reason>: The reason why the action or plan was not possible.
        """
        raise ImpossibleQuery(' '.join(args))

    def terminal(self, *args: str) -> str:
        """
        Feature: 'Terminal command execution'
        Description: Useful when you need to execute terminal commands.
        Usage: 'terminal(<term_type>, <command>)'
        - param <term_type>: The terminal type (bash,zsh, powershell, ...).
        - param <command>: The command to execute.
        """
        # TODO Check for permission before executing
        return execute_command(args[0], args[1])

    def list_contents(self, *args: str) -> str:
        """
        Feature: 'List folder contents'
        Description: Useful when you need to list folder contents.
        Usage: 'list_contents(<folder>)'
        - param <folder>: The folder name.
        """
        return list_contents(args[0])

    def open_command(self, *args: str) -> str:
        """
        Feature: 'Open files, folders and applications'
        Description: Useful when you need to open any file, folder or application.
        Usage: 'open_command(<pathname>)'
        - param <pathname>: The file, folder or application name.
        """
        return open_command(args[0])

    def check_output(self, *args: str) -> str:
        """
        Feature: 'Check output'
        Description: Useful when you introduce a command necessitating its output for subsequent actions.
        Usage: 'check_output(<question>)'
        - param <question>: The user question.
        """
        return check_output(args[0], args[1])

    def fetch(self, *args: str) -> str:
        """
        Feature: 'Time-independent database retrival'
        Description: Useful when you need to engage in casual conversations or generative prompts.
        Usage: 'fetch(<question>)'
        - param <question>: The user question or prompt.
        """
        return fetch(args[0])

    def browse(self, *args: str) -> str:
        """
        Feature: 'Internet browsing'
        Description: Useful when you need to answer questions about current events.
        Usage: 'browse(<search_query>)'
        - param <search_query>: The web search query.
        """
        return browse(args[0])

    def display(self, *args: str) -> str:
        """
        Feature: 'Useful when you need to display plain text.'
        Description: Useful when you need to display text.
        Usage: 'display(<text>, ...)'
        - param <text>: The text to be displayed.
        """
        return display(*args[:-1])

    def summarize_files(self, *args: str) -> str:
        """
        Feature: 'Summarization of files and folders'
        Description: Useful when you need to summarize files and folders.
        Usage: 'summarize_files(<folder>, <glob>)'
        - param <folder>: The folder name.
        - param <glob>: The path wildcard characters.
        """
        return summarize(args[0], args[1])

    def describe_image(self, *args: str) -> str:
        """
        Feature: 'Image analysis'
        Description: Useful when you need to describe an image.
        Usage: 'describe_image(<image_path>)'
        - param <image_path>: The image file path.
        """
        return str(NotImplementedError('This feature is not yet implemented !'))


assert (features := Actions().INSTANCE) is not None
