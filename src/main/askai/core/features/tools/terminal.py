import logging as log
import os
from functools import partial
from os.path import expandvars
from pathlib import Path
from shutil import which
from typing import Optional, Tuple

from clitt.core.term.terminal import Terminal
from hspylib.modules.application.exit_status import ExitStatus

from askai.core.askai_events import AskAiEvents
from askai.core.askai_messages import msg
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_path, media_type_of


def list_contents(folder: str) -> Optional[str]:
    """List the contents of a folder.
    :param folder: The folder to list contents from.
    """
    posix_path = Path(f"{folder.replace('~', os.getenv('HOME'))}")
    if posix_path.exists() and posix_path.is_dir():
        status, output = _execute_bash(f'ls -lht {folder} 2>/dev/null')
        if status:
            if not output:
                return f"Folder {folder} is empty!"
            return f"Showing the contents of `{folder}`: \n{output}"
    return None


def open_command(pathname: str) -> Optional[str]:
    """Open the specified path, regardless if it's a file, folder or application.
    :param pathname: The file path to open.
    """
    posix_path = Path(f"{pathname.replace('~', os.getenv('HOME'))}")

    if posix_path.exists():
        # find the best app to open the file.
        match media_type_of(pathname):
            case ('audio', _) | ('video', _):
                fn_open = partial(_execute_bash, f'ffplay -v 0 -autoexit {pathname} &>/dev/null')
            case ('text', 'plain'):
                fn_open = partial(_execute_bash, f'echo "File \\`{pathname}\\`: \n" && cat {pathname}')
            case _:
                fn_open = partial(_execute_bash, f'open {pathname} 2>/dev/null')
        status, output = fn_open()
        if status:
            if not output:
                return f"`{pathname}` was successfully opened!"
            return output
    return None


def execute_command(shell: str, command: str) -> Optional[str]:
    """Execute a terminal command using the specified language.
    :param shell: The shell type to be used.
    :param command: The command line to be executed.
    """
    match shell:
        case 'bash':
            status, output = _execute_bash(command)
            if status:
                if not output:
                    output = f"'{shell.title()}' command `{command}` successfully executed"
        case _:
            raise NotImplementedError(f"'{shell}' is not supported!")

    return output


def _execute_bash(command_line: str) -> Tuple[bool, Optional[str]]:
    """Execute the provided command line using bash.
    :param command_line: The command line to be executed in bash.
    """
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
                output = f"\n```bash\n{output}\n```"
                shared.context.push("CONTEXT", f"Please execute `{command_line}`", 'assistant')
                shared.context.push("CONTEXT", output)
            status = True
        else:
            log.error("Command failed.\nCODE=%s \nPATH=%s \nCMD=%s ", exit_code, os.getcwd(), command)
            output = msg.cmd_failed(command)
    else:
        output = msg.cmd_no_exist(command)

    return status, output
