#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.actions
      @file: actions.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""

import inspect
from functools import cached_property, lru_cache
from textwrap import dedent
from typing import Any, Optional

from askai.core.askai_messages import msg
from askai.core.features.tools.analysis import check_output
from askai.core.features.tools.browser import browse
from askai.core.features.tools.general import display_tool
from askai.core.features.tools.generation import generate_content
from askai.core.features.tools.summarization import summarize
from askai.core.features.tools.terminal import execute_command, list_contents, open_command
from askai.core.model.action_plan import ActionPlan
from askai.exception.exceptions import ImpossibleQuery, TerminatingQuery
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.metaclass.singleton import Singleton


class Actions(metaclass=Singleton):
    """This class provides the AskAI available actions."""

    INSTANCE: "Actions"

    RESERVED: list[str] = ["invoke", "enlist"]

    def __init__(self):
        self._all = dict(
            filter(
                lambda pair: pair[0] not in self.RESERVED and not pair[0].startswith("_"),
                {n: fn for n, fn in inspect.getmembers(self, predicate=inspect.ismethod)}.items(),
            )
        )

    @cached_property
    def tool_names(self) -> list[str]:
        return [str(dk) for dk in self._all.keys()]

    def invoke(self, action: ActionPlan.Action, context: str = "") -> Optional[str]:
        """Invoke the tool with its arguments and context.
        :param action: The action to be performed.
        :param context: the tool context.
        """
        try:
            if fn := self._all[action.tool]:
                args: list[Any] = action.params
                args.append(context)
                return fn(*list(map(str.strip, args)))
        except KeyError as err:
            raise ImpossibleQuery(f"Tool not found: {action.tool} => {str(err)}")

        return None

    @lru_cache
    def enlist(self) -> str:
        """Return an 'os.linesep' separated string list of feature descriptions."""
        doc_strings: str = ""
        for fn in self._all.values():
            doc_strings += f"```{dedent(fn.__doc__)}```\n\n" if fn and fn.__doc__ else ""
        return doc_strings

    def _human_approval(self) -> bool:
        """Prompt for human approval."""
        confirm_msg = msg.access_grant()
        if (resp := line_input(confirm_msg).lower()) not in ("yes", "y"):
            raise ValueError(f"Terminal command execution was not approved '{resp}' !")
        self._approved = True

        return self._approved

    def browse(self, *args: str) -> str:
        """
        Name: 'browse'
        Description: Use this tool to stay updated on the latest news and current events, particularly when you need real-time information quickly. This tool is ideal for acquiring fresh data.
        Usage: 'browse(search_query)'
          input `search_query`: The web search query in string format.
        """
        return browse(args[0])

    def check_output(self, *args: str) -> str:
        """
        Name: 'check_output'
        Description: Utilize this tool to: Analyze output from a prior tool. Examine files and folders. Review command outputs. Determine tasks, events and appointments.
        Usage: `check_output(question)`
          input `question`: The query about the output.
        """
        return check_output(args[0], args[1])

    def describe_image(self, *args: str) -> str:
        """
        Name: 'describe_image'
        Description: This tool is specially engineered for tasks necessitating the analysis of visual content in image files.
        Usage: describe_image(image_path)
          input `image_path`: The file path of the image to be analyzed.
        """
        return str(NotImplementedError("Tool 'describe_image' is not yet implemented !"))

    def generate_content(self, *args: str) -> str:
        """
        Name: 'generate_content'
        Description: This tool is specifically designed for tasks that require generating (creating) content such as, code, text, image, and others.
        Usage: generate_content(instructions, mime_type, path_name)
          input `instructions`: These are the instructions for generating content (not the content itself).
          input `mime_type`: This is the content type (use MIME types).
          input `path_name`: This is the directory path where you want to save the generated content. This parameter is optional and should be included only if you wish to save files directly to your disk. If not specified, the content will not be saved.
        """
        return generate_content(args[0], args[1], args[2])

    def final_answer(self, *args: str) -> str:
        """
        Name: 'final_answer'
        Description: Use this tool to provide your final answer. Join all messages to the user together in only one call as you can input a list of texts do be displayed.
        Usage: 'final_answer(text, ...repeat N times)'
          input `texts`: The comma separated list of texts to be displayed.
        """
        return display_tool(*args[:-1])

    def list_tool(self, *args: str) -> str:
        """
        Name: 'list_tool'
        Description: This tool is designed for retrieving and displaying the contents of a specified folder. It is useful for quickly assessing the files and subdirectories within any directory.
        Usage: 'list_tool(folder)'
          input `folder`: A string representing the name of the directory whose contents you wish to list.
        """
        return list_contents(args[0])

    def open_tool(self, *args: str) -> str:
        """
        Name: 'open_tool'
        Description: This tool is used to open or show the contents of files, folders, or applications on my system. This can be also used to play media files.
        Usage: 'open_tool(pathname)'
          input `pathname`: The file, folder or application name.
        """
        return open_command(args[0])

    def q_and_a_tool(self, *args: str) -> str:
        """
        Name: 'q_and_a_tool'
        Description: Use this tool upon specific user request. The user input **MUST CONTAIN THE KEYWORD** 'summarize'.
        Usage: summarize_tool(folder_name, glob)
          input `folder_name`: Name of the directory containing the files.
          input `glob`: Glob pattern to specify files within the folder for summarization.
        """
        return summarize(args[0], args[1])

    def terminal(self, *args: str) -> str:
        """
        Name: 'terminal'
        Description: Use this tool to execute commands directly in the user terminal or process user-provided commands efficiently. Fix any syntax errors if you find any.
        Usage: 'terminal(shell_type, command)'
          input `shell_type`: A string that specifies the type of terminal environment (e.g., bash, zsh, powershell, etc).
          input `command`: The actual commands you wish to execute in the terminal.
        """
        # TODO Check for permission before executing
        return execute_command(args[0], args[1])

    def terminate(self, *args: str) -> None:
        """
        Name: 'terminate'
        Description: Use this tool when the user decides to conclude the interaction. This function ensures a smooth and clear ending to the session, confirming user intent to terminate the dialogue.
        Usage: 'terminate(reason)'
          input `reason`: A string indicating the reason for termination.
        """
        raise TerminatingQuery(args[0])


assert (features := Actions().INSTANCE) is not None
