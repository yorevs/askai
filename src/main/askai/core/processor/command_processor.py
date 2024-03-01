import logging as log
import os
import re
from shutil import which
from typing import Tuple, Optional

from clitt.core.term.terminal import Terminal
from hspylib.modules.application.exit_status import ExitStatus
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.model.query_response import QueryResponse
from askai.core.model.terminal_command import TerminalCommand, SupportedShells, SupportedPlatforms
from askai.core.processor.ai_processor import AIProcessor
from askai.core.processor.output_processor import OutputProcessor


class CommandProcessor(AIProcessor):
    """Process a command based question process."""

    MSG: AskAiMessages = AskAiMessages.INSTANCE

    # Match most commonly used shells.
    RE_SHELLS = '(ba|c|da|k|tc|z)?sh'

    # Match a terminal command formatted in a markdown code block.
    RE_CMD = r".*`{3}(" + RE_SHELLS + ")(.+)`{3}.*"

    def __init__(self):
        self._llm: OpenAI = OpenAI(temperature=0.0, top_p=0.0)

    def __str__(self):
        return f"\"{self.query_type()}\": {self.query_desc()}"

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
        return q_type == self.query_type()

    def processor_id(self) -> str:
        return str(abs(hash(self.__class__.__name__)))

    def query_type(self) -> str:
        return self.name

    def query_desc(self) -> str:
        return (
            "Prompts that will require you to execute commands at the user's terminal "
            "(Example: list files and folders)."
    )

    def template(self) -> str:
        return AskAiPrompt.INSTANCE.read_template('command-prompt')

    def process(self, query_response: QueryResponse) -> Tuple[bool, Optional[str]]:
        status = False
        output = None
        template = PromptTemplate(
            input_variables=['os_type', 'shell', 'question'],
            template=self.template()
        )
        final_prompt: str = template.format(
            os_type=self.os_type,
            shell=self.shell,
            question=query_response.question
        )
        log.info("%s::[QUESTION] '%s'", self.name, final_prompt)
        try:
            output = self._llm(final_prompt).replace("\n", " ").strip()
            if mat := re.match(self.RE_CMD, output, re.I | re.M):
                if mat.groups() != 3 and mat.group(1) != self.shell:
                    output = self.MSG = AskAiMessages.INSTANCE.not_a_command(mat.group(1), str(self.shell))
                else:
                    status, output = self._process_command(query_response, mat.group(3).strip())
            else:
                output = self.MSG.invalid_cmd_format(output)
        except Exception as err:
            output = f"LLM returned an error: {str(err)}"
        finally:
            return status, output

    def next_in_chain(self) -> AIProcessor:
        return self.find_by_name(OutputProcessor.__name__)

    def _process_command(self, query_response: QueryResponse, cmd_line: str) -> Tuple[bool, Optional[str]]:
        """Process a terminal command.
        :param cmd_line: The command line to execute.
        """
        status = False
        command = cmd_line.split(" ")[0]
        try:
            if command and which(command):
                cmd_line = cmd_line.replace("~", os.getenv("HOME"))
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=self.MSG.executing())
                log.info("Executing command `%s'", cmd_line)
                cmd_out, exit_code = Terminal.INSTANCE.shell_exec(cmd_line, shell=True)
                if exit_code == ExitStatus.SUCCESS:
                    AskAiEvents.ASKAI_BUS.events.reply.emit(message=self.MSG.cmd_success(exit_code), erase_last=True)
                    status = True
                    if not cmd_out:
                        cmd_out = self.MSG.cmd_no_output()
                    else:
                        cmd_out = self._wrap_output(query_response, cmd_line, cmd_out)
                else:
                    cmd_out = self.MSG.cmd_failed(command)
            else:
                cmd_out = self.MSG.cmd_no_exist(command)
        except Exception as err:
            log.error(err)
            cmd_out = self.MSG.cmd_failed(command) + f" -> {str(err)}"

        return status, cmd_out

    def _wrap_output(self, query_response: QueryResponse, cmd_line: str, cmd_out: str) -> str:
        """TODO"""
        query_response.query_type = self.next_in_chain().query_type()
        query_response.require_command = False
        query_response.commands.append(TerminalCommand(cmd_line, cmd_out, self.os_type, self.shell))
        return str(query_response)
