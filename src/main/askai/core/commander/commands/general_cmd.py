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
import locale
from abc import ABC

from askai.core.askai_settings import settings
from askai.core.component.summarizer import summarizer
from askai.core.support.text_formatter import text_formatter
from clitt.core.term.terminal import Terminal
from hspylib.core.config.path_object import PathObject
from hspylib.core.tools.commons import sysout
from hspylib.modules.application.exit_status import ExitStatus

import os.path

from askai.language.language import Language


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

    @staticmethod
    def idiom(locale_str: str) -> None:
        """Set the application language.
        :param locale_str: The locale string.
        """
        try:
            if locale_str and (language := Language.of_locale(locale_str)):
                locale.setlocale(locale.LC_ALL, (language.idiom, language.encoding.val))
                settings.put("askai.preferred.language", language.idiom)
                text_formatter.cmd_print(f"Locale changed to: {language}")
            else:
                language = Language.of_locale(locale.getlocale(locale.LC_ALL))
                text_formatter.cmd_print(f"Current locale: {language}")
        except (ValueError, TypeError) as err:
            sysout(f"\n%RED%-=- Failed to set idiom: '{str(err)}'! -=-%NC%")
