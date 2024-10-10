#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.enums.run_modes
      @file: run_modes.py
   @created: Wed, 02 Oct 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from hspylib.core.enums.enumeration import Enumeration


class RunModes(Enumeration):
    """AskAI run modes"""

    ASKAI_TUI = "ASKAI_TUI"  # Interactive Terminal UI.
    ASKAI_CLI = "ASKAI_CLI"  # Interactive CLI.
    ASKAI_CMD = "ASKAI_CMD"  # Non interactive CLI (Command mode).

    def __str__(self) -> str:
        return self.name
