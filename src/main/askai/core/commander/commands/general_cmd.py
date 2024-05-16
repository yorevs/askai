#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.settings_cmd
      @file: general_cmd.py
   @created: Mon, 06 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from abc import ABC
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from clitt.core.term.terminal import Terminal
from hspylib.modules.application.exit_status import ExitStatus

import re


class GeneralCmd(ABC):
    """TODO"""

    @staticmethod
    def forget(context: str | None = None) -> None:
        """Forget entries pushed to the chat context.
        :param context: The context key; or none to forget all context.
        """
        if context:
            shared.context.clear(*(re.split(r"[;,|]", context.upper())))
        else:
            shared.context.forget()
        text_formatter.cmd_print(f"Context %GREEN%'{context.upper() or 'ALL'}'%NC% has been reset!")

    @staticmethod
    def execute(cmd_line: str | None = None) -> None:
        """Execute a terminal command.
        :param cmd_line The command line to execute.
        """
        output, exit_code = Terminal.INSTANCE.shell_exec(cmd_line, shell=True)
        if exit_code == ExitStatus.SUCCESS:
            text_formatter.cmd_print(output)
        else:
            text_formatter.cmd_print(f"Command `{cmd_line}` failed to execute: Code ({exit_code})")
