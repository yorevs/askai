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
from string import Template

from hspylib.core.metaclass.singleton import Singleton
from langchain_core.prompts import PromptTemplate

from askai.__classpath__ import _Classpath
from askai.core.askai_configs import configs
from askai.core.model.terminal_command import SupportedPlatforms, get_shell, SupportedShells, get_os, get_user
from askai.core.support.utilities import read_resource


class AskAiPrompt(metaclass=Singleton):
    """Provide the prompts used by the AskAi."""

    INSTANCE: 'AskAiPrompt' = None

    # AI Prompts directory.
    PROMPT_DIR = str(_Classpath.resource_path()) + "/assets/prompts"

    # AI Personas directory.
    PERSONA_DIR = str(_Classpath.resource_path()) + "/assets/personas"

    def __init__(self):
        self._shell: SupportedShells = get_shell()
        self._os_type: SupportedPlatforms = get_os()
        self._user: str = get_user()
        self._setup: PromptTemplate = PromptTemplate(
            input_variables=['query_types'],
            template=read_resource(self.PROMPT_DIR, "setup.txt"))

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

    def setup(self, query_types: str) -> str:
        """Return the setup prompt.
        :param query_types: A string containing al query types descriptions.
        """
        return self._setup.format(query_types=query_types)

    @lru_cache
    def read_prompt(self, template_file: str, persona_file: str) -> str:
        """Read a processor prompt template and set its persona."""
        template = Template(read_resource(self.PROMPT_DIR, template_file))
        persona = read_resource(self.PERSONA_DIR, persona_file)
        return template.substitute(persona=persona)


assert (prompt := AskAiPrompt().INSTANCE) is not None
