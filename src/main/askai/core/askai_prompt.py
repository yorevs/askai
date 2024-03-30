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
from askai.__classpath__ import _Classpath
from askai.core.askai_configs import configs
from askai.core.model.terminal_command import get_os, get_shell, get_user, SupportedPlatforms, SupportedShells
from askai.core.support.utilities import read_resource
from functools import lru_cache
from hspylib.core.metaclass.singleton import Singleton


class AskAiPrompt(metaclass=Singleton):
    """Provide the prompts used by the AskAi."""

    INSTANCE: "AskAiPrompt" = None

    # AI Prompts directory.
    PROMPT_DIR = str(_Classpath.resource_path()) + "/assets/prompts"

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
    def read_prompt(self, template_file: str) -> str:
        """Read a processor prompt template and set its persona."""
        return read_resource(self.PROMPT_DIR, template_file)


assert (prompt := AskAiPrompt().INSTANCE) is not None
