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
from typing import List, Optional, Tuple

from clitt.core.term.terminal import Terminal
from hspylib.modules.application.exit_status import ExitStatus
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.model.processor_response import ProcessorResponse
from askai.core.model.query_type import QueryType
from askai.core.model.terminal_command import TerminalCommand
from askai.core.processor.processor_base import AIProcessor
from askai.core.support.langchain_support import lc_llm
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

    def name(self) -> str:
        return type(self).__name__

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
        template = PromptTemplate(
            input_variables=['os_type', 'shell', 'idiom', 'question'], template=self.template())
        final_prompt: str = template.format(
            os_type=prompt.os_type, shell=prompt.shell,
            idiom=shared.idiom, question=query_response.question)
        ctx: str = shared.context.flat("CONTEXT")
        log.info("Command::[QUESTION] '%s'  context=%s", final_prompt, ctx)

        chat_prompt = ChatPromptTemplate.from_messages([("system", "{query}\n\n{context}")])
        chain = create_stuff_documents_chain(lc_llm.create_chat_model(), chat_prompt)
        context = [Document(ctx)]

        if response := chain.invoke({"query": final_prompt, "context": context}):
            log.debug("Command::[RESPONSE] Received from AI: %s.", response)
            shell, command = extract_command(response)
            if command:
                if shell and shell != prompt.shell:
                    output = msg.not_a_command(str(prompt.shell), command)
                else:
                    status, output = self._process_command(query_response, command)
            else:
                output = msg.invalid_cmd_format(response)
        else:
            output = msg.llm_error(response)

        return status, output

    def _process_command(self, query_response: ProcessorResponse, cmd_line: str) -> Tuple[bool, Optional[str]]:
        """Process a terminal command.
        :param query_response: The response for the query asked by the user.
        :param cmd_line: The command line to execute.
        """
        status = False
        command = cmd_line.split(" ")[0].strip()

        if command and which(command):
            cmd_line = expandvars(cmd_line.replace("~/", f"{os.getenv('HOME')}/").strip())
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.executing())
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
                    shared.context.push("CONTEXT", f"\n\nUser:\n{query_response.question}")
                    shared.context.push("CONTEXT", f"\n\nCommand `{cmd_line}' output:\n```\n{output}```")
                    output = self._wrap_output(query_response, cmd_line, output)
            else:
                log.error("Command failed.\nCODE=%s \nPATH=%s \nCMD=%s ", exit_code, os.getcwd(), cmd_line)
                output = msg.cmd_failed(cmd_line)
            status = True
        else:
            output = msg.cmd_no_exist(command)

        return status, output
