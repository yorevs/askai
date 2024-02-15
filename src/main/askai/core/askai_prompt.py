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
from hspylib.core.metaclass.singleton import Singleton
from string import Template

from askai.utils.utilities import read_prompt


class AskAiPrompt(metaclass=Singleton):
    """Provide the prompts used by the AskAi."""

    INSTANCE = None

    def __init__(self):
        self._shell = os.getenv("HHS_MY_SHELL", "bash")
        self._os_type = os.getenv("HHS_MY_OS_RELEASE", "linux")
        self._setup = Template(read_prompt("homesetup.txt"))

    def setup(self) -> str:
        return self._setup.substitute(
            shell=self._shell,
            os_type=self._os_type
        )
