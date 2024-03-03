import logging as log
import os
import re
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


class CommandProcessor(AIProcessor):
    """Process a command based question process."""

    # Match most commonly used shells.
    RE_SHELLS = '(ba|c|da|k|tc|z)?sh'

    # Match a terminal command formatted in a markdown code block.
    RE_CMD = r'.*`{3}(' + RE_SHELLS + ')(.+)`{3}.*'

    # Match a file or folder path.
    RE_PATH = r'.* ((\w:|[~.])?(/.+)+(.*)?) ?.*'

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
        last_dir = str(shared.context["LAST_DIR"][0].content)
        template = PromptTemplate(
            input_variables=['os_type', 'shell', 'last_dir'], template=self.template())
        final_prompt: str = template.format(
            os_type=self.os_type, shell=self.shell, last_dir=last_dir)
        shared.context.set("SETUP", final_prompt, 'system')
        shared.context.set("QUESTION", query_response.question)
        context: List[dict] = shared.context.get_many("SETUP", "OUTPUT", "ANALYSIS", "QUESTION")
        log.info("%s::[QUESTION] '%s'", self.name, context)
        try:
            if (response := shared.engine.ask(context, temperature=0.0, top_p=0.0)) and response.is_success():
                output = response.reply_text().replace("\n", " ").strip()
                if mat := re.match(self.RE_CMD, output, re.I | re.M):
                    CacheService.save_query_history()
                    shell = mat.group(1).strip()
                    if mat.groups() != 3 and shell != self.shell:
                        output = AskAiMessages.INSTANCE.not_a_command(shell, str(self.shell))
                    else:
                        status, output = self._process_command(query_response, mat.group(3).strip())
                else:
                    output = AskAiMessages.INSTANCE.invalid_cmd_format(output)
            else:
                output = AskAiMessages.INSTANCE.llm_error(response.reply_text())
        except Exception as err:
            output = AskAiMessages.INSTANCE.llm_error(str(err))
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
        try:
            if command and which(command):
                cmd_line = cmd_line.replace("~", os.getenv("HOME")).strip()
                AskAiEvents.ASKAI_BUS.events.reply.emit(message=AskAiMessages.INSTANCE.executing())
                log.info("Executing command `%s'", cmd_line)
                cmd_out, exit_code = Terminal.INSTANCE.shell_exec(cmd_line, shell=True)
                if exit_code == ExitStatus.SUCCESS:
                    cmd_path = re.search(self.RE_PATH, cmd_line)
                    if cmd_path:
                        cmd_path = cmd_path.group(1)
                        shared.context.set("LAST_DIR", f"Last used directory: '{cmd_path}'", 'assistant')
                    AskAiEvents.ASKAI_BUS.events.reply.emit(
                        message=AskAiMessages.INSTANCE.cmd_success(exit_code), erase_last=True
                    )
                    status = True
                    shared.context.set("COMMAND", query_response.question)
                    if not cmd_out:
                        cmd_out = AskAiMessages.INSTANCE.cmd_no_output()
                    else:
                        shared.context.set("OUTPUT", cmd_out)
                        cmd_out = self._wrap_output(query_response, cmd_line, cmd_out)
                else:
                    cmd_out = AskAiMessages.INSTANCE.cmd_failed(command)
            else:
                cmd_out = AskAiMessages.INSTANCE.cmd_no_exist(command)
        except Exception as err:
            status = False
            log.error(err)
            cmd_out = AskAiMessages.INSTANCE.cmd_failed(command) + f"&br;&br;&error; -> {str(err)}&br;"

        return status, cmd_out

    def _wrap_output(self, query_response: QueryResponse, cmd_line: str, cmd_out: str) -> str:
        """TODO"""
        query_response.query_type = self.next_in_chain().query_type()
        query_response.require_command = False
        query_response.commands.append(TerminalCommand(cmd_line, cmd_out, self.os_type, self.shell))
        return str(query_response)
