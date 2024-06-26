#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.features.tools.terminal
      @file: terminal.py
   @created: Mon, 01 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
import logging as log
import os
import re
from functools import partial
from os.path import expandvars
from shutil import which
from typing import Tuple

from clitt.core.term.terminal import Terminal
from hspylib.core.config.path_object import PathObject
from hspylib.modules.application.exit_status import ExitStatus

from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.features.rag.rag import resolve_x_refs
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import extract_path, media_type_of


def list_contents(folder: str, filters: str) -> str:
    """List the contents of a folder.
    :param folder: The folder to list contents from.
    :param filters: The optional listing filters (file glob).
    """
    def _build_filters_() -> str:
        return '\\( ' + "-o".join([f" -name \"{f}\" " for f in re.split(r'[,;|]\s?', filters)]).strip() + ' \\)'
    path_obj = PathObject.of(folder)
    if path_obj.exists and path_obj.is_dir:
        cmd_line: str = (
            f'find {folder} -maxdepth 1 -type f {_build_filters_() if filters else ""} '
            f'-exec ls -lLht {{}} + 2>/dev/null | sort -k9,9')
        status, output = _execute_bash(cmd_line)
        if status:
            if output:
                return msg.translate(f"Listing the contents of: `{folder}`:\n\n{output}\n")
            return '' if filters else f"The folder: '{folder}' is empty."

    return msg.translate(f"Error: Could not list folder: '{folder}'!")


def open_command(path_name: str) -> str:
    """Open the specified path, regardless if it's a file, folder or application.
    :param path_name: The file path to open.
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
        mtype = media_type_of(path_name)
        match mtype:
            case ("audio", _) | ("video", _):
                fn_open = partial(_execute_bash, f"ffplay -v 0 -autoexit {path_name} &>/dev/null")
            case ("text", _):
                fn_open = partial(_execute_bash, f"cat {path_name}")
            case ("inode", "directory"):
                fn_open = partial(list_contents, path_name)
            case _:
                fn_open = partial(_execute_bash, f"open {path_name} 2>/dev/null")
        status, output = fn_open()
        if status:
            if not output:
                output = msg.translate(f"{mtype[0].title()}: `{path_name}` was successfully opened!")
            else:
                output = msg.translate(f"Showing the contents of: `{path_name}`:\n\n{output}\n")
            return output
    else:
        return msg.translate(f"Error: File was not found: '{path_name}'!")

    return msg.translate(f"Error: Failed to open: '{path_name}'!")


def execute_command(shell: str, command_line: str) -> str:
    """Execute a terminal command using the specified language.
    :param shell: The shell type to be used.
    :param command_line: The command line to be executed.
    """
    match shell:
        case "bash":
            status, output = _execute_bash(command_line)
        case _:
            raise NotImplementedError(msg.translate(f"'{shell}' is not supported!"))

    return output or (msg.cmd_success(command_line) if status else msg.cmd_failed(command_line))


def _execute_bash(command_line: str) -> Tuple[bool, str]:
    """Execute the provided command line using bash.
    :param command_line: The command line to be executed in bash.
    """
    status, output = False, ''
    if (command := command_line.split(" ")[0].strip()) and which(command):
        command = expandvars(command_line.replace("~/", f"{os.getenv('HOME')}/").strip())
        log.info("Executing command `%s'", command)
        events.reply.emit(message=msg.executing(command_line), verbosity="debug")
        output, exit_code = Terminal.INSTANCE.shell_exec(command, shell=True)
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
            output = msg.cmd_failed(command)
    else:
        output = msg.cmd_no_exist(command)

    return status, output
