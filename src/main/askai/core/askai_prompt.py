#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.utils
      @file: askai_prompt.py
   @created: Mon, 22 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
from functools import lru_cache
from pathlib import Path

from hspylib.core.enums.charset import Charset
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.core.tools.text_tools import ensure_endswith
from langchain_core.prompts import PromptTemplate

from askai.__classpath__ import _Classpath
from askai.core.askai_configs import configs
from askai.core.model.terminal_command import SupportedPlatforms, get_shell, SupportedShells, get_os, get_user
from askai.core.processor.ai_processor import AIProcessor


class AskAiPrompt(metaclass=Singleton):
    """Provide the prompts used by the AskAi."""

    INSTANCE: 'AskAiPrompt' = None

    # AI Prompts directory.
    PROMPT_DIR = str(_Classpath.resource_path()) + "/assets/prompts"

    def __init__(self):
        self._shell: SupportedShells = get_shell()
        self._os_type: SupportedPlatforms = get_os()
        self._user: str = get_user()
        self._query_types: str = AIProcessor.find_query_types()
        self._setup: PromptTemplate = PromptTemplate(
            input_variables=['query_types'], template=self.read_template("setup.txt"))

    @property
    def os_type(self) -> SupportedPlatforms:
        return self._os_type

    @property
    def shell(self) -> SupportedShells:
        return self._shell

    @property
    def user(self) -> str:
        return self._user

    @property
    def idiom(self) -> str:
        return f"{configs.language.name} ({configs.language.country})"

    def setup(self) -> str:
        return self._setup.format(query_types=self._query_types)

    @lru_cache
    def read_template(self, filename: str) -> str:
        """Read the prompt template specified by the filename.
        :param filename: The filename of the prompt.
        """
        filename = f"{self.PROMPT_DIR}/{ensure_endswith(filename, '.txt')}"
        check_argument(file_is_not_empty(filename), f"Prompt file does not exist: {filename}")
        return Path(filename).read_text(encoding=Charset.UTF_8.val)


assert (prompt := AskAiPrompt().INSTANCE) is not None
