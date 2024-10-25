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
    def app_info() -> None:
        """Display some useful application information."""
        display_text(shared.app_info, markdown=False)

    @staticmethod
    def execute(cmd_line: str | None = None) -> None:
        """Execute a terminal command.
        :param cmd_line: The command line to execute (optional).
        """
        output, err_out, exit_code = Terminal.INSTANCE.shell_exec(cmd_line, shell=True)
        if exit_code == ExitStatus.SUCCESS:
            text_formatter.commander_print(output)
        else:
            display_text(f"\n%RED%Command `{cmd_line}` failed. Error({err_out})  Code ({exit_code})%NC%")

    @staticmethod
    def summarize(folder: str, glob: str) -> None:
        """Generate a summarization of files and folder contents.
        :param folder: The base folder from which the summarization will be generated.
        :param glob: The glob pattern specifying which files or folders to include in the summarization.
        """
        sum_dir: PathObject = PathObject.of(folder)
        if os.path.exists(sum_dir.abs_dir):
            if summarizer.generate(sum_dir.abs_dir, glob):
                text_formatter.commander_print(f"Summarization complete. Folder: *{folder}*  Glob: *{glob}* !")
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
                text_formatter.commander_print(f"Locale changed to: {language}")
            else:
                language = Language.of_locale(locale.getlocale(locale.LC_ALL))
                text_formatter.commander_print(f"Current locale: {language}")
        except (ValueError, TypeError) as err:
            display_text(f"\n%RED%-=- Failed to set idiom: '{str(err)}'! -=-%NC%")

    @staticmethod
    def translate(from_lang: Language, to_lang: Language, *texts: str) -> None:
        """Translate text from the source language to the target language.
        :param from_lang: The source language.
        :param to_lang: The target language.
        :param texts: The texts to be translated.
        """
        translator = AskAiMessages.get_translator(from_lang, to_lang)
        list(map(display_text, map(translator.translate, texts)))
