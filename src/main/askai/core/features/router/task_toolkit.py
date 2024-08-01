#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.actions
      @file: task_toolkit.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.core.askai_messages import msg
from askai.core.features.router.tools.analysis import query_output
from askai.core.features.router.tools.browser import browse
from askai.core.features.router.tools.general import display_tool, final_answer
from askai.core.features.router.tools.generation import generate_content, save_content
from askai.core.features.router.tools.summarization import summarize
from askai.core.features.router.tools.terminal import execute_command, list_contents, open_command
from askai.core.features.router.tools.vision import image_captioner
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import TerminatingQuery
from clitt.core.tui.line_input.line_input import line_input
from functools import lru_cache
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.metaclass.singleton import Singleton
from langchain_core.tools import BaseTool, StructuredTool
from textwrap import dedent
from typing import Callable

import inspect
import logging as log


class AgentToolkit(metaclass=Singleton):
    """This class provides the AskAI task agent tools."""

    INSTANCE: "AgentToolkit"

    RESERVED: list[str] = ["tools"]

    def __init__(self):
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
        """Create the LangChain agent tool.
        :param fn: The function that provides the tool implementation.
        """
        return StructuredTool.from_function(
            func=fn,
            name=fn.__name__,
            description=f"```{dedent(fn.__doc__)}```\n\n" if fn and fn.__doc__ else "",
            return_direct=True,
        )

    def browse(self, search_query: str) -> str:
        """Use this tool to browse the internet or to stay informed about the latest news and current events, especially when you require up-to-date information quickly. It is especially effective for accessing the most recent data available online.
        Usage: `browse(search_query)`
        :param search_query: The web search query in string format.
        """
        return browse(search_query)

    def query_output(self, output_query: str) -> str:
        """Use this tool to analyze textual content to identify the presence of files, folders, and applications. It is designed to process and analyze content that is already available in textual form, but not to read or extract file contents directly.
        Usage: `query_output(query)`
        :param output_query: The query regarding the output. Prefer using "Identify <file types or name or textual content>".
        """
        return query_output(output_query)

    def image_captioner(self, image_path: str) -> str:
        """Use this tool to provide a textual description of a visual content, such as, image files.
        Usage: image_captioner(image_path)
        :param image_path: The absolute path of the image file to be analyzed.
        """
        return image_captioner(image_path)

    def generate_content(self, instructions: str, mime_type: str, filepath: AnyPath) -> str:
        """Use this tool for tasks that require generating any kind of content, such as, code and text, image, etc.
        Usage: generate_content(instructions, mime_type)
        :param instructions: The instructions for generating the content.
        :param mime_type: The generated content type (use MIME types).
        :param filepath: Optional file path for saving the content.
        """
        return generate_content(instructions, mime_type, filepath)

    def save_content(self, filepath: AnyPath) -> str:
        """Use this tool to save generated content into disk (program, script, text, image, etc).
        Usage: save_content(filepath)
        :param filepath: The path where you want to save the content.
        """
        return save_content(filepath)

    def display_tool(self, texts: list[str] | str) -> str:
        """
        Name: 'Display Tool'
        Description: Use this tool to display textual information.
        Usage: 'display_tool(text, ...repeat N times)'
        :param texts: The comma separated list of texts to be displayed.
        """
        return display_tool(*(texts if isinstance(texts, list) else [texts]))

    def direct_answer(self, question: str, answer: str) -> str:
        """Use this tool to execute terminal commands or process user-provided commands."
        Usage: 'direct_answer(answer)'
        :param question: The original user question.
        :param answer: Your direct answer to the user.
        """
        args = {'user': shared.username, 'idiom': shared.idiom, 'context': answer, 'question': question}
        return final_answer("taius-jarvis", [k for k in args.keys()], **args)

    def list_tool(self, folder: str, filters: str | None = None) -> str:
        """
        Name: 'List Folder'
        Description: Use this tool to access the contents of a specified folder.
        Usage: 'list_tool(folder, filters)'
        :param folder: The absolute path of the folder whose contents you wish to list or access.
        :param filters: Optional Parameter: Specify a comma-separated list of file glob to filter the results (e.g., "*.*, *.txt").
        """
        return list_contents(folder, filters)

    def open_tool(self, path_name: str) -> str:
        """Use this tool to open, read (show) content of files, and also, to playback any media files.
        Usage: 'open_tool(path_name)'
        :param path_name: The absolute file, folder, or application path name.
        """
        return open_command(path_name)

    def summarize(self, folder: str, glob: str) -> str:
        """Use this tool only when the user explicitly requests a summary of files and folders.
        Usage: summarize(folder_name, glob)
        :param folder: The base name of the folder containing the files to be summarized.
        :param glob: The glob expression to specify files to be included for summarization.
        """
        return summarize(folder, glob)

    def terminal(self, shell_type: str, command: str) -> str:
        """Use this tool to execute terminal commands or process user-provided commands."
        Usage: 'terminal(shell_type, command)'
        :param shell_type: The type of the shell (e.g. bash, zsh, powershell, etc).
        :param command: The actual commands you wish to execute in the terminal.
        """
        # TODO Check for permission before executing
        return execute_command(shell_type, command)

    def shutdown(self, reason: str) -> None:
        """Use this tool when the user provides a query that indicates he wants to conclude the interaction (e.g. bye, exit).
        Usage: 'shutdown(reason)'
        :param reason: The reason for termination.
        """
        raise TerminatingQuery(reason)


assert (features := AgentToolkit().INSTANCE) is not None
