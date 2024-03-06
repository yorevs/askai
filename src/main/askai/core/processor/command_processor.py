import logging as log
import os
from shutil import which
from typing import Tuple, Optional, List

from clitt.core.term.terminal import Terminal
from hspylib.modules.application.exit_status import ExitStatus
from langchain_core.prompts import PromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.component.cache_service import CacheService
from askai.core.model.query_response import QueryResponse
from askai.core.model.terminal_command import TerminalCommand, SupportedShells, SupportedPlatforms
from askai.core.processor.ai_processor import AIProcessor
from askai.core.processor.output_processor import OutputProcessor
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_path, extract_command


class CommandProcessor(AIProcessor):
    """Process a command based question process."""

    def __str__(self):
        return f"'{self.query_type()}': {self.query_desc()}"

    @property
    def name(self) -> str:
        return type(self).__name__

    @property
    def shell(self) -> SupportedShells:
        return AskAiPrompt.INSTANCE.shell

    @property
    def os_type(self) -> SupportedPlatforms:
        return AskAiPrompt.INSTANCE.os_type

    def supports(self, q_type: str) -> bool:
        return q_type in [self.query_type()]

    def processor_id(self) -> str:
        return str(abs(hash(self.__class__.__name__)))

    def query_type(self) -> str:
        return self.name

    def query_desc(self) -> str:
        return (
            "Prompts that will require you to execute commands at the user's terminal. These prompts may involve "
            "file, folder and application management, listing, device assessment or inquiries."
        )

    def template(self) -> str:
        return AskAiPrompt.INSTANCE.read_template('command-prompt')

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        template = PromptTemplate(
            input_variables=['os_type', 'shell'], template=self.template())
        final_prompt: str = template.format(
            os_type=self.os_type, shell=self.shell)
        shared.context.set("SETUP", final_prompt, 'system')
        shared.context.set("QUESTION", query_response.question)
        context: List[dict] = shared.context.get_many("CONTEXT", "SETUP", "QUESTION")
        log.info("Command::[QUESTION] '%s'  context=%s", query_response.question, context)
        try:
            if (response := shared.engine.ask(context, temperature=0.0, top_p=0.0)) and response.is_success:
                log.debug('Command::[RESPONSE] Received from AI: %s.', response)
                shell, command = extract_command(response.message)
                if command:
                    if shell and shell != self.shell:
                        output = AskAiMessages.INSTANCE.not_a_command(str(self.shell), command)
                    else:
                        CacheService.save_query_history()
                        status, output = self._process_command(query_response, command)
                else:
                    output = AskAiMessages.INSTANCE.invalid_cmd_format(response.message)
            else:
                output = AskAiMessages.INSTANCE.llm_error(response.message)
        finally:
            return status, output

    def next_in_chain(self) -> AIProcessor:
        return AIProcessor.get_by_name(OutputProcessor.__name__)

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
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=AskAiMessages.INSTANCE.executing(cmd_line))
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
                    AskAiEvents.ASKAI_BUS.events.reply.emit(
                        message=AskAiMessages.INSTANCE.cmd_success(exit_code), erase_last=True)
                    if not cmd_out:
                        cmd_out = AskAiMessages.INSTANCE.cmd_no_output()
                    else:
                        shared.context.push("CONTEXT", f"Command `{cmd_line}' output:\n\n```\n{cmd_out}\n```")
                        cmd_out = self._wrap_output(query_response, cmd_line, cmd_out)
                else:
                    log.error(
                        "Command failed.\nCODE=%s \nPATH=%s \nCMD=%s ", exit_code, os.getcwd(), cmd_line)
                    cmd_out = AskAiMessages.INSTANCE.cmd_failed(cmd_line)
                status = True
            else:
                cmd_out = AskAiMessages.INSTANCE.cmd_no_exist(command)
        finally:
            return status, cmd_out

    def _wrap_output(self, query_response: QueryResponse, cmd_line: str, cmd_out: str) -> str:
        """TODO"""
        query_response.query_type = self.next_in_chain().query_type()
        query_response.require_command = False
        query_response.commands.append(TerminalCommand(cmd_line, cmd_out, self.os_type, self.shell))
        return str(query_response)
