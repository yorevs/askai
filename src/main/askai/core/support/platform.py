"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: platform.py
   @created: Thu, 29 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from functools import lru_cache
from os.path import basename
from typing import Literal, TypeAlias

import os
import platform

SupportedPlatforms: TypeAlias = Literal["linux", "windows", "darwin"] | None

SupportedShells: TypeAlias = Literal["bash", "csh", "dash", "ksh", "tcsh", "zsh", "sh"] | None


@lru_cache
def get_os() -> SupportedPlatforms:
    os_name = platform.system().lower()
    return os_name if os_name and os_name in ["linux", "windows", "darwin"] else None


@lru_cache
def get_shell() -> SupportedShells:
    shell = basename(os.getenv("SHELL", "bash")).lower()
    return shell if shell and shell in ["bash", "csh", "dash", "ksh", "tcsh", "zsh", "sh"] else None


@lru_cache
def get_user() -> str:
    return os.getenv("USER", "user")
