import logging as log
import os
from shutil import which
from typing import Optional, Tuple

from clitt.core.term.terminal import Terminal
from hspylib.modules.application.exit_status import ExitStatus

from askai.core.askai_messages import AskAiMessages
from askai.core.askai_prompt import AskAiPrompt
from askai.core.model.query_response import QueryResponse
from askai.core.processor.ai_processor import AIProcessor


class CommandProcessor(AIProcessor):
    """Process a command based question process."""

    MSG = AskAiMessages.INSTANCE

    def __init__(self, query_response: QueryResponse = None):
        self._response = query_response

    def __str__(self):
        return f"\"{self.query_name()}\": {self.query_desc()}"

    def supports(self, q_type: str) -> bool:
        return q_type == self.query_name

    def processor_id(self) -> str:
        return str(abs(hash(self.__class__.__name__)))

    def query_name(self) -> str:
        return f"Type-{self.processor_id()}"

    def query_desc(self) -> str:
        return (
            "Prompts that will require you to execute commands at the user's terminal "
            "(Example: list files and folders)."
    )

    def prompt(self) -> str:
        return AskAiPrompt.INSTANCE.read_prompt('command-prompt')

    def process(self, query_response: QueryResponse) -> Tuple[bool, str]:
        return True, self._response.response

    def prev_in_chain(self) -> Optional[AIProcessor]:
        return None

    def next_in_chain(self) -> Optional[AIProcessor]:
        return None

    def _process_command(self, cmd_line: str) -> None:
        """Process a terminal command.
        :param cmd_line: The command line to execute.
        """
        if (command := cmd_line.split(" ")[0]) and which(command):
            cmd_line = cmd_line.replace("~", os.getenv("HOME"))
            self._reply(self.MSG.executing())
            log.info("Executing command `%s'", cmd_line)
            output, exit_code = Terminal.INSTANCE.shell_exec(cmd_line, shell=True)
            if exit_code == ExitStatus.SUCCESS:
                self._reply(self.MSG.cmd_success(exit_code))
                if output:
                    self._ask_and_reply(f"%COMMAND OUTPUT: \n\n{output}")
                else:
                    self._reply(self.MSG.cmd_no_output())
            else:
                self._reply(self.MSG.cmd_failed(command))
        else:
            self._reply(self.MSG.cmd_no_exist(command))

    def _reply(self, param):
        pass

    def _ask_and_reply(self, param):
        pass
