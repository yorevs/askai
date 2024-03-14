#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.processor
      @file: command_processor.py
   @created: Fri, 23 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import logging as log
import os
from shutil import which
from typing import Optional, Tuple

from clitt.core.term.terminal import Terminal
from hspylib.modules.application.exit_status import ExitStatus
from langchain_core.prompts import PromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperatures import Temperatures
from askai.core.model.chat_context import ContextRaw
from askai.core.model.query_response import QueryResponse
from askai.core.model.terminal_command import TerminalCommand
from askai.core.processor.ai_processor import AIProcessor
from askai.core.processor.output_processor import OutputProcessor
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_command, extract_path


class CommandProcessor(AIProcessor):
    """Process command request prompts."""

    def __init__(self):
        super().__init__("command-prompt", "command-persona")

    def query_desc(self) -> str:
        return (
            "Prompts that will require you to execute commands at the user's terminal. These prompts may involve "
            "file, folder and application management, listing, device assessment or inquiries."
        )

    def bind(self, next_in_chain: "AIProcessor"):
        pass  # Avoid re-binding the next in chain processor.

    def next_in_chain(self) -> AIProcessor:
        return AIProcessor.get_by_name(OutputProcessor.__name__)

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        template = PromptTemplate(input_variables=["os_type", "shell"], template=self.template())
        final_prompt: str = template.format(os_type=prompt.os_type, shell=prompt.shell)
        shared.context.set("SETUP", final_prompt, "system")
        shared.context.set("QUESTION", query_response.question)
        context: ContextRaw = shared.context.join("CONTEXT", "SETUP", "QUESTION")
        log.info("Command::[QUESTION] '%s'  context=%s", query_response.question, context)

        if (response := shared.engine.ask(context, *Temperatures.DATA_ANALYSIS.value)) and response.is_success:
            log.debug("Command::[RESPONSE] Received from AI: %s.", response)
            shell, command = extract_command(response.message)
            if command:
                if shell and shell != prompt.shell:
                    output = msg.not_a_command(str(prompt.shell), command)
                else:
                    status, output = self._process_command(query_response, command)
            else:
                output = msg.invalid_cmd_format(response.message)
        else:
            output = msg.llm_error(response.message)

        return status, output

    def _process_command(self, query_response: QueryResponse, cmd_line: str) -> Tuple[bool, Optional[str]]:
        """Process a terminal command.
        :param query_response: The response for the query asked by the user.
        :param cmd_line: The command line to execute.
        """
        status = False
        command = cmd_line.split(" ")[0].strip()
        cmd_out = None
        try:
            if command and which(command):
                cmd_line = cmd_line.replace("~", os.getenv("HOME")).strip()
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.executing(cmd_line))
                log.info("Executing command `%s'", cmd_line)
                cmd_out, exit_code = Terminal.INSTANCE.shell_exec(cmd_line, shell=True)
                if exit_code == ExitStatus.SUCCESS:
                    log.info("Command succeeded.\nCODE=%s \nPATH: %s \nCMD: %s ", exit_code, os.getcwd(), cmd_line)
                    if _path_ := extract_path(cmd_line):
                        if _path_:
                            os.chdir(_path_)
                            log.info("Current directory changed to '%s'", _path_)
                        else:
                            log.warning("Directory '%s' does not exist. Curdir unchanged!", _path_)
                    AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.cmd_success(exit_code), erase_last=True)
                    if not cmd_out:
                        cmd_out = msg.cmd_no_output()
                    else:
                        shared.context.push("CONTEXT", f"Command `{cmd_line}' output:\n\n```\n{cmd_out}\n```")
                        cmd_out = self._wrap_output(query_response, cmd_line, cmd_out)
                else:
                    log.error("Command failed.\nCODE=%s \nPATH=%s \nCMD=%s ", exit_code, os.getcwd(), cmd_line)
                    cmd_out = msg.cmd_failed(cmd_line)
                status = True
            else:
                cmd_out = msg.cmd_no_exist(command)
        finally:
            return status, cmd_out

    def _wrap_output(self, query_response: QueryResponse, cmd_line: str, cmd_out: str) -> str:
        """Wrap the output into a new string to be forwarded to the next processor.
        :param query_response: The query response provided by the AI.
        :param cmd_line: The command line that was executed by this processor.
        """
        query_response.query_type = self.next_in_chain().query_type()
        query_response.require_summarization = False
        query_response.require_internet = False
        query_response.commands.append(TerminalCommand(cmd_line, cmd_out, prompt.os_type, prompt.shell))
        return str(query_response)
