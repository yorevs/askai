"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: os_utils.py
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
    """Retrieve the current operating system platform.
    :return: The current operating system as a `SupportedPlatforms` literal value.
    """
    os_name = platform.system().lower()
    return os_name if os_name and os_name in ["linux", "windows", "darwin"] else None


@lru_cache
def get_shell() -> SupportedShells:
    """Retrieve the current shell being used.
    :return: The current shell as a `SupportedShells` literal value.
    """
    shell = basename(os.getenv("SHELL", "bash")).lower()
    return shell if shell and shell in ["bash", "csh", "dash", "ksh", "tcsh", "zsh", "sh"] else None


@lru_cache
def get_user() -> str:
    """Retrieve the current user's username.
    :return: The username of the current user as a string. Returns "user" if the username is not found.
    """
    return os.getenv("USER", "user")
