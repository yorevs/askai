#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.actions
      @file: actions.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

import inspect
from functools import lru_cache
from textwrap import dedent
from typing import Callable

from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.metaclass.singleton import Singleton
from langchain_core.tools import BaseTool, StructuredTool

from askai.core.askai_messages import msg
from askai.core.features.tools.analysis import query_output
from askai.core.features.tools.browser import browse
from askai.core.features.tools.general import display_tool
from askai.core.features.tools.generation import generate_content
from askai.core.features.tools.summarization import summarize
from askai.core.features.tools.terminal import execute_command, list_contents, open_command
from askai.core.features.tools.vision import image_captioner
from askai.exception.exceptions import TerminatingQuery


class Actions(metaclass=Singleton):
    """This class provides the AskAI available actions."""

    INSTANCE: "Actions"

    RESERVED: list[str] = ["agent_tools"]

    def __init__(self):
        """TODO"""
        self._all = dict(
            filter(
                lambda pair: pair[0] not in self.RESERVED and not pair[0].startswith("_"),
                {n: fn for n, fn in inspect.getmembers(self, predicate=inspect.ismethod)}.items(),
            )
        )

    @lru_cache
    def agent_tools(self) -> list[BaseTool]:
        """TODO"""
        return [self._create_agent_tool(v) for _, v in self._all.items()]

    def _human_approval(self) -> bool:
        """Prompt for human approval."""
        confirm_msg = msg.access_grant()
        if (resp := line_input(confirm_msg).lower()) not in ("yes", "y"):
            raise ValueError(f"Terminal command execution was not approved '{resp}' !")
        self._approved = True

        return self._approved

    def _create_agent_tool(self, fn: Callable) -> BaseTool:
        """Create the LangChain agent tool."""

        return StructuredTool.from_function(
            fn,
            name=fn.__name__,
            description=f"```{dedent(fn.__doc__)}```\n\n" if fn and fn.__doc__ else "",
            return_direct=True,
        )

    def browse(self, search_query: str) -> str:
        """
        Name: 'browse'
        Description: Use this tool when you need to answer questions about current events.
        Usage: 'browse(search_query)'
          input `search_query`: The web search query in string format.
        """
        return browse(search_query)

    def query_output(self, question: str) -> str:
        """
        Name: 'query_output'
        Description: Use this tool to verify the presence of files and folders, and conduct text analysis.
        Usage: `query_output(question)`
          input `question`: The query regarding the output. Do not provide terminal commands for this input.
        """
        return query_output(question)

    def image_captioner(self, image_path: str) -> str:
        """
        Name: 'image_captioner'
        Description: Use this tool to analyze visual content of a single image file.
        Usage: image_captioner(image_path)
          input `image_path`: The file path of the image to be analyzed.
        """
        return image_captioner(image_path)

    def generate_content(self, instructions: str, mime_type: str, path_name: str) -> str:
        """
        Name: 'generate_content'
        Description: This tool is specifically designed for tasks that require generating (creating) content such as, code, text, image, and others.
        Usage: generate_content(instructions, mime_type, path_name)
          input `instructions`: These are the instructions for generating content (not the content itself).
          input `mime_type`: This is the content type (use MIME types).
          input `path_name`: This is the directory path where you want to save the generated content. This parameter is optional and should be included only if you wish to save files directly to your disk. If not specified, the content will not be saved.
        """
        return generate_content(instructions, mime_type, path_name)

    def display_tool(self, answer: list[str] | str) -> str:
        """
        Name: 'display_tool'
        Description: Use this tool to provide general conversation responses, to display text or to output your final answer.
        Usage: 'final_answer(text, ...repeat N times)'
          input `texts`: The comma separated list of texts to be displayed.
        """
        return display_tool(*(answer if isinstance(answer, list) else [answer]))

    def list_tool(self, folder: str) -> str:
        """
        Name: 'list_tool'
        Description: This tool is designed for retrieving and displaying the contents of a specified folder. It is useful for quickly assessing the files and subdirectories within any directory.
        Usage: 'list_tool(folder)'
          input `folder`: A string representing the name of the directory whose contents you wish to list.
        """
        return list_contents(folder)

    def open_tool(self, path_name: str) -> str:
        """
        Name: 'open_tool'
        Description: This tool is used to open or show the contents of files, folders, or applications on my system. This can be also used to play media files.
        Usage: 'open_tool(pathname)'
          input `path_name`: The file, folder or application name.
        """
        return open_command(path_name)

    def q_and_a_tool(self, folder_name: str, glob) -> str:
        """
        Name: 'q_and_a_tool'
        Description: Use this tool only when the user explicitly requests a summary. The user's request must include the keyword 'summarize' for the tool to be engaged. Ensure that the tool is not activated if the keyword 'summarize' is not present in the user's input.
        Usage: summarize_tool(folder_name, glob)
          input `folder_name`: Name of the directory containing the files.
          input `glob`: Glob pattern to specify files within the folder for summarization.
        """
        return summarize(folder_name, glob)

    def terminal(self, shell_type: str, command: str) -> str:
        """
        Name: 'terminal'
        Description: Use this tool to execute terminal commands directly within the user shell or process user-provided commands efficiently.
        Usage: 'terminal(shell_type, command)'
          input `shell_type`: A string that specifies the type of terminal environment (e.g., bash, zsh, powershell, etc).
          input `command`: The actual commands you wish to execute in the terminal.
        """
        # TODO Check for permission before executing
        return execute_command(shell_type, command)

    def terminate(self, reason: str) -> None:
        """
        Name: 'terminate'
        Description: Use this tool when the user decides to conclude the interaction. This function ensures a smooth and clear ending to the session, confirming user intent to terminate the dialogue.
        Usage: 'terminate(reason)'
          input `reason`: A string indicating the reason for termination.
        """
        raise TerminatingQuery(reason)


assert (features := Actions().INSTANCE) is not None
