#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.router.tools.terminal
      @file: terminal.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.model.ai_reply import AIReply
from askai.core.router.evaluation import resolve_x_refs
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_path, media_type_of
from clitt.core.term.terminal import terminal
from functools import partial
from hspylib.core.config.path_object import PathObject
from hspylib.modules.application.exit_status import ExitStatus
from os.path import expandvars
from shutil import which
from typing import Tuple

import logging as log
import os
import re


def list_contents(folder: str, filters: str = None) -> str:
    """List the contents of a folder.
    :param folder: The folder to list contents from.
    :param filters: The optional listing filters (file glob).
    :return: A list of the contents in the folder that match the filters.
    """

    def _build_filters_() -> str:
        return "\\( " + "-o".join([f' -name "{f}" ' for f in re.split(r"[,;|]\s?", filters)]).strip() + " \\)"

    path_obj = PathObject.of(folder)
    if path_obj.exists and path_obj.is_dir:
        cmd_line: str = (
            f'find {folder} -maxdepth 1 -type f {_build_filters_() if filters else ""} '
            f"! -name '.*' -exec ls -oLhtu {{}} + 2>/dev/null | sort -k9,9"
        )
        status, output = execute_bash(cmd_line)
        if status:
            if output:
                return f"Listing the contents of: `{folder}`:\n\n{output}\n"
            return "" if filters else f"The folder: '{folder}' is empty."

    return f"Error: Could not list folder: '{folder}'!"


def open_command(path_name: str) -> str:
    """Open the specified path, regardless if it's a file, folder or application.
    :param path_name: The file path to open.
    :return: A string telling whether the path was successfully opened or not.
    """

    posix_path: PathObject = PathObject.of(path_name)
    if not posix_path.exists:
        # Attempt to resolve cross-references
        if history := str(shared.context.flat("HISTORY") or ""):
            if (x_referenced := resolve_x_refs(path_name, history)) and x_referenced != shared.UNCERTAIN_ID:
                x_ref_path: PathObject = PathObject.of(x_referenced)
                posix_path: PathObject = x_ref_path if x_ref_path.exists else posix_path

    if posix_path.exists:
        # find the best app to open the file.
        path_name: str = str(posix_path)
        mtype: tuple[str, ...] = media_type_of(path_name) or ("text", "plain")
        match mtype:
            case ("audio", _) | ("video", _):
                fn_open = partial(execute_bash, f"ffplay -v 0 -autoexit {path_name} &>/dev/null")
            case ("text", _):
                fn_open = partial(execute_bash, f"cat {path_name}")
            case ("inode", "directory"):
                fn_open = partial(list_contents, path_name)
            case _:
                fn_open = partial(execute_bash, f"open {path_name} 2>/dev/null")
        status, output = fn_open()
        if status:
            if not output:
                output = f"{mtype[0].title()}: `{path_name}` was successfully opened!"
            else:
                output = f"Showing the contents of: `{path_name}`:\n\n{output}\n"
            return output
    else:
        return f"Error: File was not found: '{path_name}'!"

    return f"Error: Failed to open: '{path_name}'!"


def execute_command(shell: str, command_line: str) -> str:
    """Execute a terminal command using the specified shell.
    :param shell: The shell type to be used.
    :param command_line: The command line to be executed.
    :return: The output of the executed command.
    """
    match shell:
        case "bash":
            status, output = execute_bash(command_line)
        case _:
            raise NotImplementedError(f"'{shell}' is not supported!")

    return output or (msg.cmd_success(command_line) if status else msg.cmd_failed(command_line))


def execute_bash(command_line: str) -> Tuple[bool, str]:
    """Execute the provided command line using bash.
    :param command_line: The command line to be executed in bash.
    :return: A tuple containing a boolean indicating success or failure and the output or error message.
    """
    status, output = False, ""
    if (command := command_line.split(" ")[0].strip()) and which(command):
        command = expandvars(command_line.replace("~/", f"{os.getenv('HOME')}/").strip())
        log.info("Executing command `%s'", command)
        events.reply.emit(reply=AIReply.full(msg.executing(command_line)))
        output, err_out, exit_code = terminal.shell_exec(command, shell=True)
        if exit_code == ExitStatus.SUCCESS:
            log.info("Command succeeded: \n|-CODE=%s \n|-PATH: %s \n|-CMD: %s ", exit_code, os.getcwd(), command)
            if _path_ := extract_path(command):
                os.chdir(_path_)
                log.info("Current directory changed to '%s'", _path_)
            else:
                log.warning("Directory '%s' does not exist. Current dir unchanged!", _path_)
            if output:
                output = f"\n```bash\n{output}```\n"
            status = True
        else:
            log.error("Command failed.\nCODE=%s \nPATH=%s \nCMD=%s ", exit_code, os.getcwd(), command)
            output = msg.cmd_failed(command, err_out)
    else:
        output = msg.cmd_no_exist(command)

    return status, output
