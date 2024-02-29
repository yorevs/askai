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
import os
from functools import lru_cache
from pathlib import Path
from string import Template

from hspylib.core.enums.charset import Charset
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.core.tools.text_tools import ensure_endswith
from langchain_core.prompts import PromptTemplate

from askai.__classpath__ import _Classpath
from askai.core.processor.ai_processor import AIProcessor


class AskAiPrompt(metaclass=Singleton):
    """Provide the prompts used by the AskAi."""

    INSTANCE: 'AskAiPrompt' = None

    # AI Prompts directory.
    PROMPT_DIR = str(_Classpath.resource_path()) + "/assets/prompts"

    def __init__(self):
        self._shell: str = os.getenv("HHS_MY_SHELL", "bash")
        self._os_type: str = os.getenv("HHS_MY_OS_RELEASE", "linux")
        self._query_types: str = AIProcessor.get_query_types()
        self._setup: PromptTemplate = PromptTemplate(
            input_variables=["query_types", "question"],
            template=self.read_prompt("setup.txt")
        )

    @property
    def os_type(self) -> str:
        return self._os_type.lower()

    @property
    def shell(self) -> str:
        return self._shell.lower()

    def setup(self, question: str) -> str:
        return self._setup.format(query_types=self._query_types, question=question)

    @lru_cache
    def read_prompt(self, filename: str) -> str:
        """Read the prompt specified by the filename.
        :param filename: The filename of the prompt.
        """
        filename = f"{self.PROMPT_DIR}/{ensure_endswith(filename, '.txt')}"
        check_argument(file_is_not_empty(filename), f"Prompt file does not exist: {filename}")
        return Path(filename).read_text(encoding=Charset.UTF_8.val)

    @lru_cache
    def read_template(self, filename: str) -> Template:
        """Read the template specified by the filename.
        :param filename: The filename of the prompt.
        """
        return Template(self.read_prompt(filename))


assert AskAiPrompt().INSTANCE is not None
