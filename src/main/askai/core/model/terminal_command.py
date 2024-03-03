"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: terminal_command.py
   @created: Thu, 29 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import json
import os
from dataclasses import dataclass
import platform
from os.path import basename
from typing import Literal, TypeAlias

SupportedPlatforms: TypeAlias = Literal["linux", "windows", "darwin"] | None

SupportedShells: TypeAlias = Literal["bash", "csh", "dash", "ksh", "tcsh", "zsh", "sh"] | None


def get_os() -> SupportedPlatforms:
    os_name = platform.system().lower()
    return os_name if os_name and os_name in ["linux", "windows", "darwin"] else None


def get_shell() -> SupportedShells:
    shell = basename(os.getenv("SHELL", "bash")).lower()
    return shell if shell and shell in ["bash", "csh", "dash", "ksh", "tcsh", "zsh", "sh"] else None


def get_user() -> str:
    return os.getenv("USER", "user")


@dataclass
class TerminalCommand:
    """Keep track of the executed terminal commands."""

    cmd_line: str
    cmd_out: str
    os: SupportedPlatforms = get_os()
    shell: SupportedShells = get_shell()

    def __str__(self):
        return json.dumps(self.__dict__, default=lambda obj: obj.__dict__)
