import logging as log
import os
from typing import Optional

from clitt.core.term.terminal import Terminal
from hspylib.modules.application.exit_status import ExitStatus
from langchain_core.tools import tool

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.processor.tools.output import process_output
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_path


@tool
def terminal(language: str, command_line: str) -> Optional[str]:
    """Execute a terminal command using the specified language.
    :param language: The command language.
    :param command_line: The command line to be executed.
    """
    match language:
        case 'bash':
            return execute_shell(command_line)
        case _:
            raise NotImplemented(f"Language '{language}' is not supported")


def execute_shell(command_line: str) -> Optional[str]:
    """TODO"""

    AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.executing())
    log.info("Executing command `%s'", command_line)
    output, exit_code = Terminal.INSTANCE.shell_exec(command_line, shell=True)

    if exit_code == ExitStatus.SUCCESS:
        log.info("Command succeeded.\nCODE=%s \nPATH: %s \nCMD: %s ", exit_code, os.getcwd(), command_line)
        if _path_ := extract_path(command_line):
            if _path_:
                os.chdir(_path_)
                log.info("Current directory changed to '%s'", _path_)
            else:
                log.warning("Directory '%s' does not exist. Current dir unchanged!", _path_)
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.cmd_success(exit_code), erase_last=True)
        if not output:
            output = msg.cmd_no_output()
        else:
            shared.context.push("CONTEXT", f"\n\nCommand `{command_line}' output:\n```\n{output}```")
    else:
        log.error("Command failed.\nCODE=%s \nPATH=%s \nCMD=%s ", exit_code, os.getcwd(), command_line)
        output = msg.cmd_failed(command_line)

    return process_output(command_line, output)
