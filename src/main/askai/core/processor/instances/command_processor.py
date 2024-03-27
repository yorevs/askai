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
from functools import lru_cache
from os.path import expandvars
from shutil import which
from typing import Optional, Tuple, List

from clitt.core.term.terminal import Terminal
from hspylib.modules.application.exit_status import ExitStatus
from langchain_core.prompts import PromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.engine.openai.temperatures import Temperatures
from askai.core.model.chat_context import ContextRaw
from askai.core.model.processor_response import ProcessorResponse
from askai.core.model.query_type import QueryType
from askai.core.model.terminal_command import TerminalCommand
from askai.core.processor.processor_base import AIProcessor
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_command, extract_path


class CommandProcessor:
    """Process command request prompts."""

    @staticmethod
    def _wrap_output(query_response: ProcessorResponse, cmd_line: str, cmd_out: str) -> str:
        """Wrap the output into a new string to be forwarded to the next processor.
        :param query_response: The query response provided by the AI.
        :param cmd_line: The command line that was executed by this processor.
        """
        query_response.query_type = QueryType.OUTPUT_QUERY.value
        query_response.require_summarization = False
        query_response.forwarded = True
        query_response.commands.append(TerminalCommand(cmd_line, cmd_out, prompt.os_type, prompt.shell))

        return str(query_response)

    @staticmethod
    def q_type() -> str:
        return QueryType.COMMAND_QUERY.value

    def __init__(self):
        self._template_file: str = "command-prompt"
        self._next_in_chain: str = QueryType.OUTPUT_QUERY.proc_name
        self._supports: List[str] = [self.q_type()]

    def supports(self, query_type: str) -> bool:
        return query_type in self._supports

    def next_in_chain(self) -> Optional[str]:
        return self._next_in_chain

    def bind(self, next_in_chain: AIProcessor):
        pass

    @lru_cache
    def template(self) -> str:
        return prompt.read_prompt(self._template_file)

    def process(self, query_response: ProcessorResponse) -> Tuple[bool, Optional[str]]:
        status = False
        template = PromptTemplate(input_variables=["os_type", "shell"], template=self.template())
        final_prompt: str = template.format(os_type=prompt.os_type, shell=prompt.shell)
        shared.context.set("SETUP", final_prompt, "system")
        shared.context.set("QUESTION", f"\n\nQuestion: {query_response.question}\n\nHelpful Answer:")
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

    def _process_command(self, query_response: ProcessorResponse, cmd_line: str) -> Tuple[bool, Optional[str]]:
        """Process a terminal command.
        :param query_response: The response for the query asked by the user.
        :param cmd_line: The command line to execute.
        """
        status = False
        command = cmd_line.split(" ")[0].strip()
        output = None
        try:
            if command and which(command):
                cmd_line = expandvars(cmd_line.replace("~/", f"{os.getenv('HOME')}/").strip())
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.executing(cmd_line))
                log.info("Executing command `%s'", cmd_line)
                output, exit_code = Terminal.INSTANCE.shell_exec(cmd_line, shell=True)
                if exit_code == ExitStatus.SUCCESS:
                    log.info("Command succeeded.\nCODE=%s \nPATH: %s \nCMD: %s ", exit_code, os.getcwd(), cmd_line)
                    if _path_ := extract_path(cmd_line):
                        if _path_:
                            os.chdir(_path_)
                            log.info("Current directory changed to '%s'", _path_)
                        else:
                            log.warning("Directory '%s' does not exist. Curdir unchanged!", _path_)
                    AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.cmd_success(exit_code), erase_last=True)
                    if not output:
                        output = msg.cmd_no_output()
                    else:
                        shared.context.set("CONTEXT", f"Command `{cmd_line}' output:\n\n```\n{output}\n```")
                        output = self._wrap_output(query_response, cmd_line, output)
                else:
                    log.error("Command failed.\nCODE=%s \nPATH=%s \nCMD=%s ", exit_code, os.getcwd(), cmd_line)
                    output = msg.cmd_failed(cmd_line)
                status = True
            else:
                output = msg.cmd_no_exist(command)
        finally:
            return status, output
