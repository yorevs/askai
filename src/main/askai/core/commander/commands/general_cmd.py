#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.general_cmd
      @file: general_cmd.py
   @created: Mon, 06 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from abc import ABC
from askai.core.component.summarizer import summarizer
from askai.core.support.text_formatter import text_formatter
from clitt.core.term.terminal import Terminal
from hspylib.core.config.path_object import PathObject
from hspylib.core.tools.commons import sysout
from hspylib.modules.application.exit_status import ExitStatus

import os.path


class GeneralCmd(ABC):
    """TODO"""

    @staticmethod
    def execute(cmd_line: str | None = None) -> None:
        """Execute a terminal command.
        :param cmd_line The command line to execute.
        """
        output, exit_code = Terminal.INSTANCE.shell_exec(cmd_line, shell=True)
        if exit_code == ExitStatus.SUCCESS:
            text_formatter.cmd_print(output)
        else:
            sysout(f"\n%RED%-=- Command `{cmd_line}` failed to execute: Code ({exit_code}) -=-%NC%")

    @staticmethod
    def summarize(folder: str, glob: str) -> None:
        """Generate a summarization of the folder contents.
        :param folder: The base folder of the summarization.
        :param glob: The glob pattern or file of the summarization.
        """
        sum_dir: PathObject = PathObject.of(folder)
        if os.path.exists(sum_dir.abs_dir):
            if summarizer.generate(sum_dir.abs_dir, glob):
                text_formatter.cmd_print(f"Summarization complete. Folder: *{folder}*  Glob: *{glob}* !")
            else:
                sysout(f"\n%RED%-=- Failed to summarize. Folder: {folder}  Glob: {glob} ! -=-%NC%")
        else:
            sysout(f"\n%RED%-=- Folder '{folder}' does not exist! -=-%NC%")
