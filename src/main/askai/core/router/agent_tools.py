#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.router
      @file: agent_tools.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import inspect
import logging as log
import os
import re
from functools import lru_cache
from textwrap import dedent
from typing import Callable, Optional

from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.metaclass.singleton import Singleton
from langchain_core.tools import BaseTool, StructuredTool

from askai.core.askai_messages import msg
from askai.core.router.tools.analysis import query_output
from askai.core.router.tools.browser import browse, open_url
from askai.core.router.tools.general import display_tool
from askai.core.router.tools.generation import generate_content, save_content
from askai.core.router.tools.summarization import summarize
from askai.core.router.tools.terminal import execute_command, list_contents, open_command
from askai.core.router.tools.vision import image_captioner, parse_image_caption, capture_screenshot
from askai.core.router.tools.webcam import webcam_capturer, webcam_identifier, CAPTION_TEMPLATE
from askai.exception.exceptions import TerminatingQuery


class AgentTools(metaclass=Singleton):
    """This class serves as the toolkit for AskAI task agents, providing essential tools and functionalities required
    for their tasks.
    """

    INSTANCE: "AgentTools"

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
        """Return a cached list of LangChain base tools.
        :return: A list of BaseTool's instances available for use.
        """
        tools: list[BaseTool] = [self._create_structured_tool(v) for _, v in self._all.items()]

        log.debug("Available tools: are: '%s'", tools)

        return tools

    @property
    def available_tools(self) -> str:
        avail_list: list[str] = list()
        for t in self.tools():
            if match := re.search(r"^```(.*?)^\s*Usage:", t.description, re.DOTALL | re.MULTILINE):
                avail_list.append(f"**{t.name}::** " + re.sub(r"\s{2,}", " ", match.group(1).strip()))
        return os.linesep.join(avail_list)

    def _human_approval(self) -> bool:
        """Prompt for human approval."""
        confirm_msg = msg.access_grant()
        if (resp := line_input(confirm_msg).lower()) not in ("yes", "y"):
            raise ValueError(f"Terminal command execution was not approved '{resp}' !")
        self._approved = True

        return self._approved

    def _create_structured_tool(self, fn: Callable) -> BaseTool:
        """Create a LangChain agent tool based on the provided function.
        :param fn: The function that implements the tool's behavior.
        :return: An instance of BaseTool configured with the provided function.
        """
        return StructuredTool.from_function(
            func=fn,
            name=fn.__name__,
            description=f"```{dedent(fn.__doc__)}```\n\n" if fn and fn.__doc__ else "",
            return_direct=True,
        )

    def browse(self, search_query: str) -> Optional[str]:
        """Use this tool to browse the internet for the latest news and current events, particularly when up-to-date
        information is needed quickly. This tool is especially effective for accessing the most recent data available
        online.
        Usage: `browse(search_query)`
        :param search_query: The user search query as a string. It's important to keep the user keywords as is.
        :return: A string containing the results of the web search, or None if no relevant results are found.
        """
        return browse(search_query)

    def open_url(self, url: str) -> str:
        """Use this tool to open the browser landing at a specific website, specified by the given URL. This is not
        useful for searching the web.
        Usage: `open_url(url)`
        :param url: The URL to be opened.
        :return: A string telling whether the URL was successfully opened or not.
        """
        return open_url(url)

    def query_output(self, output_query: str) -> str:
        """Use this tool to analyze textual content, and to identify files, folders, and applications. This
        tool is NOT designed to directly read or extract file or folder contents.
        Usage: `query_output(output_query)`
        :param output_query: The query regarding the output. Use "Identify <file types, names, or textual content>".
        :return: A string containing the results of the analysis based on the query.
        """
        return query_output(output_query)

    def image_captioner(self, image_path: str) -> str:
        """Use this tool to generate a textual description of visual content, such as image files.
        Usage: `image_captioner(image_path)`
        :param image_path: The absolute path of the image file to be analyzed.
        :return: A string containing the generated caption describing the image.
        """
        image_caption: list[str] = parse_image_caption(image_captioner(image_path))
        return CAPTION_TEMPLATE.substitute(
            image_path=image_path, image_caption=os.linesep.join(image_caption) if image_caption else ""
        )

    def webcam_capturer(self, photo_name: str | None, detect_faces: bool = False, question: str | None = None) -> str:
        """Capture a photo via the webcam, and save it locally. Also provide a description of the objects and people
        depicted in the picture. An additional question may address specific details regarding the photo.
        Usage: `webcam_capturer(photo_name, detect_faces, question)`
        :param photo_name: Optional name of the photo image file (without the extension).
        :param detect_faces: Whether to detect and describe all faces in the photo (default is False).
        :param question: Optional specific question about the photo taken (default is None).
        :return: The file path of the saved JPEG image.
        """
        return webcam_capturer(photo_name, detect_faces, question)

    def webcam_identifier(self) -> str:
        """Capture a photo via the webcam and compare it to a pre-stored set of images to determine if the current
        subject matches any stored faces.
        Usage: `webcam_identifier()`
        :return: A string containing the identification and description of the person.
        """
        return webcam_identifier()

    def screenshot(self, path_name: AnyPath | None = None, save_dir: AnyPath | None = None) -> str:
        """Capture a screenshot and save it to the specified path.
        Usage: `screenshot(path_name, load_dir)`
        :param path_name: Optional path name of the captured screenshot.
        :param save_dir: Optional directory to save the screenshot.
        :return: The path to the saved screenshot.
        """
        return capture_screenshot(path_name, save_dir)

    def generate_content(self, instructions: str, mime_type: str, filepath: AnyPath) -> str:
        """Use this tool to generate various types of content, such as code, text, images, etc. This tool processes
        descriptive instructions to create the specified content type and can optionally save it to a file.
        Usage: `generate_content(instructions, mime_type, filepath)`
        :param instructions: Descriptive instructions on how to create the content (not the content itself).
        :param mime_type: The MIME type representing the type of content to generate.
        :param filepath: The optional file path where the generated content will be saved.
        :return: The generated content as a string.
        """
        return generate_content(instructions, mime_type, filepath)

    def save_content(self, filepath: AnyPath) -> str:
        """Save previously generated content to disk, such as programs, scripts, text, images, etc. This tool is used
        to persist content that was generated using the `generate_content` tool.
        Usage: `save_content(filepath)`
        :param filepath: The path where you want to save the content.
        :return: The absolute path name of the saved file.
        """
        return save_content(filepath)

    def direct_answer(self, texts: list[str] | str) -> str:
        """Provide and display text as a direct answer to the user. This tool is used to present one or more pieces of
        text directly to the user.
        Usage: `direct_answer(text, ...repeat N times)`
        :param texts: A list of texts or a single text string to be displayed.
        :return: A string containing all provided texts concatenated together.
        """
        return display_tool(*(texts if isinstance(texts, list) else [texts]))

    def list_tool(self, folder: str, filters: str | None = None) -> str:
        """Access and list the contents of a specified folder. This tool is used to retrieve the contents of a folder,
        optionally filtering the results based on specified criteria.
        Usage: `list_tool(folder, filters)`
        :param folder: The absolute path of the folder whose contents you wish to list or access.
        :param filters: Optional parameter: A comma-separated list of file globs to filter results (e.g., "*.*, *.txt").
        :return: A string listing the contents of the folder, filtered by the provided criteria if applicable.
        """
        return list_contents(folder, filters)

    def open_tool(self, path_name: str) -> str:
        """Open and display the content of files, or playback media files, and also execute applications. This tool is
        used to open a file, folder, or application, read its contents, or play back media files.
        Usage: `open_tool(path_name)`
        :param path_name: The absolute path of the file, folder, or application to be opened.
        :return: The output generated by the open command, such as file content or playback status.
        """
        return open_command(path_name)

    def summarize(self, folder: str, glob: str) -> str:
        """Summarize the contents of files and folders based on user requests. This tool should be used only when the
        user explicitly requests a summary of files and folders, not for summarizing textual content.
        Usage: `summarize(folder, glob)`
        :param folder: The base path of the folder containing the files to be summarized.
        :param glob: The glob expression to specify which files should be included in the summary.
        :return: A string containing the summary of the specified files and folders.
        """
        return summarize(folder, glob)

    def terminal(self, shell_type: str, command: str) -> str:
        """Execute terminal commands or process user-provided commands using the specified shell. This tool is used to
        run commands in a terminal environment based on the provided shell type.
        Usage: `terminal(shell_type, command)`
        :param shell_type: The type of shell to use (e.g., bash, zsh, powershell, etc.).
        :param command: The command or set of commands to execute in the terminal.
        :return: The output of the executed terminal command(s) as a string.
        """
        # TODO Check for permission before executing
        return execute_command(shell_type, command)

    def shutdown(self, reason: str) -> None:
        """Conclude the interaction based on the user's intent to end the session (e.g., bye, exit). This tool is used
        to gracefully shut down the interaction when the user indicates a desire to terminate the session.
        Usage: `shutdown(reason)`
        :param reason: The reason for terminating the session.
        """
        raise TerminatingQuery(reason)


assert (features := AgentTools().INSTANCE) is not None
