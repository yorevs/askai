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

from askai.core.askai_messages import msg
from askai.core.features.tools.analysis import query_output
from askai.core.features.tools.browser import browse
from askai.core.features.tools.general import display_tool
from askai.core.features.tools.generation import generate_content
from askai.core.features.tools.summarization import summarize
from askai.core.features.tools.terminal import execute_command, list_contents, open_command
from askai.core.features.tools.vision import image_captioner
from askai.exception.exceptions import TerminatingQuery
from clitt.core.tui.line_input.line_input import line_input
from functools import lru_cache
from hspylib.core.metaclass.singleton import Singleton
from langchain_core.tools import BaseTool, StructuredTool
from textwrap import dedent
from typing import Callable

import inspect
import logging as log


class Actions(metaclass=Singleton):
    """This class provides the AskAI available actions."""

    INSTANCE: "Actions"

    RESERVED: list[str] = ["tools"]

    def __init__(self):
        """TODO"""
        self._all: dict[str, Callable] = dict(
            filter(
                lambda pair: pair[0] not in self.RESERVED and not pair[0].startswith("_"),
                {n: fn for n, fn in inspect.getmembers(self, predicate=inspect.ismethod)}.items(),
            )
        )

    @lru_cache
    def tools(self) -> list[BaseTool]:
        """Return a list of Langchain base tools."""
        tools: list[BaseTool] = [self._create_structured_tool(v) for _, v in self._all.items()]

        log.debug("Available tools: are: '%s'", tools)

        return tools

    def _human_approval(self) -> bool:
        """Prompt for human approval."""
        confirm_msg = msg.access_grant()
        if (resp := line_input(confirm_msg).lower()) not in ("yes", "y"):
            raise ValueError(f"Terminal command execution was not approved '{resp}' !")
        self._approved = True

        return self._approved

    def _create_structured_tool(self, fn: Callable) -> BaseTool:
        """Create the LangChain agent tool."""
        return StructuredTool.from_function(
            fn,
            name=fn.__name__,
            description=f"```{dedent(fn.__doc__)}```\n\n" if fn and fn.__doc__ else "",
            return_direct=True,
        )

    def browse(self, search_query: str) -> str:
        """
        Name: 'Google Search'
        Description: Use this tool to browse the internet or to stay informed about the latest news and current events, especially when you require up-to-date information quickly. It is especially effective for accessing the most recent data available online.
        Usage: 'browse(search_query)'
          input `search_query`: The web search query in string format.
        """
        return browse(search_query)

    def query_output(self, query: str) -> str:
        """
        Name: 'Analyze Output'
        Description: Use this tool to analyze textual content to identify the presence of files, folders, and applications. It is designed to process and analyze content that is already available in textual form, but not to read or extract file contents directly.
        Usage: `query_output(query)`
          input `query`: The query regarding the output. Prefer using "Identify <file types or name or textual content>".
        """
        return query_output(query)

    def image_captioner(self, image_path: str) -> str:
        """
        Name: 'Describe Image'
        Description: Use this tool to provide a textual description of a visual content, such as, image files.
        Usage: image_captioner(image_path)
          input `image_path`: The file path of the image to be analyzed.
        """
        return image_captioner(image_path)

    def generate_content(self, instructions: str, mime_type: str, path_name: str) -> str:
        """
        Name: 'Generate Content'
        Description: Use this tool for tasks that require generating content such as, code and text, image, and others.
        Usage: generate_content(instructions, mime_type, path_name)
          input `instructions`: These are the instructions for generating the content.
          input `mime_type`: This is the generated content type (use MIME types).
          input `path_name`: This is the file path where you want to save the generated content. This param is optional and must be used when you intend to save the generated content locally.
        """
        return generate_content(instructions, mime_type, path_name)

    def display_tool(self, answer: list[str] | str) -> str:
        """
        Name: 'Display Tool'
        Description: Use this tool to display textual information.
        Usage: 'display_tool(text, ...repeat N times)'
          input `texts`: The comma separated list of texts to be displayed.
        """
        return display_tool(*(answer if isinstance(answer, list) else [answer]))

    def list_tool(self, folder: str) -> str:
        """
        Name: 'List Folder'
        Description: Use this tool to access the contents of a specified folder.
        Usage: 'list_tool(folder)'
          input `folder`: A string representing the name of the directory whose contents you wish to list.
        """
        return list_contents(folder)

    def open_tool(self, path_name: str) -> str:
        """
        Name: 'Open Tool'
        Description: Use this tool to open, show or read content of files. This can be also be to play media files.
        Usage: 'open_tool(pathname)'
          input `path_name`: The absolute file, folder, or application path name.
        """
        return open_command(path_name)

    def summarize(self, folder_name: str, glob) -> str:
        """
        Name: 'Summarize Tool'
        Description: Use this tool only when the user explicitly requests a summary of files and folders.
        Usage: summarize(folder_name, glob)
          input `folder_name`: Name of the base directory containing the files.
          input `glob`: Glob expression to specify files within the folder for summarization.
        """
        return summarize(folder_name, glob)

    def terminal(self, shell_type: str, command: str) -> str:
        """
        Name: 'Terminal Command'
        Description: Use this tool to execute terminal commands or process user-provided commands. This is also useful when no other tool is suitable to answer the user's request."
        Usage: 'terminal(shell_type, command)'
          input `shell_type`: A string that specifies the type of shell type (e.g. bash, zsh, powershell, etc).
          input `command`: The actual commands you wish to execute in the terminal.
        """
        # TODO Check for permission before executing
        return execute_command(shell_type, command)

    def terminate(self, reason: str) -> None:
        """
        Name: 'Task Complete (Shutdown)'
        Description: Use this tool when the user decides to conclude the interaction.
        Usage: 'terminate(reason)'
          input `reason`: A string indicating the reason for termination.
        """
        raise TerminatingQuery(reason)


assert (features := Actions().INSTANCE) is not None
