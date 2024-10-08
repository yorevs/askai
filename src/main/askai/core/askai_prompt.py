#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.askai_prompt
      @file: askai_prompt.py
   @created: Mon, 22 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.support.os_utils import get_os, get_shell, get_user, SupportedPlatforms, SupportedShells
from askai.core.support.utilities import read_resource
from functools import lru_cache
from hspylib.core.metaclass.singleton import Singleton


class AskAiPrompt(metaclass=Singleton):
    """Provide the prompts used by the AskAi."""

    INSTANCE: "AskAiPrompt"

    # AI Prompts directory.
    PROMPT_DIR = str(classpath.resource_path) + "/prompts"

    def __init__(self):
        self._shell: SupportedShells = get_shell()
        self._os_type: SupportedPlatforms = get_os()
        self._user: str = get_user()

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

    @lru_cache
    def read_prompt(self, template_file: str, prompt_dir: str = None) -> str:
        """Read a processor prompt template.
        :param template_file: The name of the template file to read.
        :param prompt_dir: Optional directory where the template file is located.
        :return: The content of the prompt template as a string.
        """
        return read_resource(prompt_dir or self.PROMPT_DIR, template_file)

    def append_path(self, path: str) -> str:
        """Return the PROMPT_DIR with the extra path appended.
        :param path: The path to append to PROMPT_DIR.
        :return: The concatenated path.
        """
        return f"{self.PROMPT_DIR}/{path}"


assert (prompt := AskAiPrompt().INSTANCE) is not None
