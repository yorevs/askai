#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.general_cmd
      @file: general_cmd.py
   @created: Mon, 06 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from abc import ABC

from askai.core.askai_messages import AskAiMessages
from askai.core.askai_settings import settings
from askai.core.component.summarizer import summarizer
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text
from askai.language.language import Language
from clitt.core.term.terminal import Terminal
from hspylib.core.config.path_object import PathObject
from hspylib.modules.application.exit_status import ExitStatus

import locale
import os.path


class GeneralCmd(ABC):
    """Provides general command functionalities."""

    @staticmethod
    def execute(cmd_line: str | None = None) -> None:
        """Execute a terminal command.
        :param cmd_line The command line to execute.
        """
        output, exit_code = Terminal.INSTANCE.shell_exec(cmd_line, shell=True)
        if exit_code == ExitStatus.SUCCESS:
            text_formatter.cmd_print(output)
        else:
            display_text(f"\n%RED%-=- Command `{cmd_line}` failed to execute: Code ({exit_code}) -=-%NC%")

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
                display_text(f"\n%RED%-=- Failed to summarize. Folder: {folder}  Glob: {glob} ! -=-%NC%")
        else:
            display_text(f"\n%RED%-=- Folder '{folder}' does not exist! -=-%NC%")

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
            display_text(f"\n%RED%-=- Failed to set idiom: '{str(err)}'! -=-%NC%")

    @staticmethod
    def app_info() -> None:
        """Display some useful application information."""
        display_text(shared.app_info)

    @staticmethod
    def translate(from_lang: Language, to_lang: Language, *texts: str) -> None:
        """Translate a text from the source language to the target language.
        :param from_lang: The source idiom.
        :param to_lang: The target idiom.
        :param texts: The texts to be translated.
        """
        translator = AskAiMessages.get_translator(from_lang, to_lang)
        list(map(display_text, map(translator.translate, texts)))

