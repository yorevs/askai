import logging as log
import os
from os.path import expandvars
from pathlib import Path
from shutil import which
from typing import Optional, Tuple

from clitt.core.term.terminal import Terminal
from hspylib.modules.application.exit_status import ExitStatus

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_path


def list_contents(folder: str) -> Optional[str]:
    """List the contents of a folder.
    :param folder: The folder to list contents from.
    """
    posix_path = Path(folder.replace('~', os.getenv('HOME')))
    if posix_path.exists() and posix_path.is_dir():
        status, output = _execute_shell(f'ls -lht {folder} 2>/dev/null')
        if status:
            return f"Showing the contents of `{folder}`: \n{output}"
        else:
            f"Failed to list from: '{folder}'"

    return f"Directory {folder} {'is not a directory' if posix_path.exists() else 'does not exist!'}!"


def open_command(pathname: str) -> Optional[str]:
    """Open the specified path, regardless if it's a file, folder or application.
    :param pathname: The file path to open.
    """
    posix_path = Path(pathname.replace('~', os.getenv('HOME')))
    if posix_path.exists():
        _, output = _execute_shell(f'open {pathname} 2>/dev/null')
        return output

    return f"Path '{pathname}' does not exist!"


def execute_command(shell: str, command: str) -> Optional[str]:
    """Execute a terminal command using the specified language.
    :param shell: The shell type to be used.
    :param command: The command line to be executed.
    """
    match shell:
        case 'bash':
            _, output = _execute_shell(command)
        case _:
            raise NotImplemented(f"'{shell}' is not supported")

    return output


def _execute_shell(command_line: str) -> Tuple[bool, Optional[str]]:
    """TODO"""
    status = False
    if (command := command_line.split(" ")[0].strip()) and which(command):
        command = expandvars(command_line.replace("~/", f"{os.getenv('HOME')}/").strip())
        log.info("Executing command `%s'", command)
        AskAiEvents.ASKAI_BUS.events.reply.emit(message=msg.executing(command_line), verbosity='debug')
        output, exit_code = Terminal.INSTANCE.shell_exec(command, shell=True)
        if exit_code == ExitStatus.SUCCESS:
            log.info("Command succeeded.\nCODE=%s \nPATH: %s \nCMD: %s ", exit_code, os.getcwd(), command)
            if _path_ := extract_path(command):
                os.chdir(_path_)
                log.info("Current directory changed to '%s'", _path_)
            else:
                log.warning("Directory '%s' does not exist. Current dir unchanged!", _path_)
            if not output:
                output = msg.cmd_success(command_line, exit_code)
            else:
                output = f"```bash\n{output}```"
                shared.context.push("CONTEXT", command_line, 'assistant')
                shared.context.push("CONTEXT", output)
            status = True
        else:
            log.error("Command failed.\nCODE=%s \nPATH=%s \nCMD=%s ", exit_code, os.getcwd(), command)
            output = msg.cmd_failed(command)
    else:
        output = msg.cmd_no_exist(command)

    return status, output
