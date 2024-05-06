#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.settings_cmd
      @file: general_cmd.py
   @created: Mon, 06 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from abc import ABC

from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter


class GeneralCmd(ABC):
    """TODO"""

    @staticmethod
    def forget(context: str | None = None) -> None:
        """TODO"""
        shared.context.forget(context)
        text_formatter.cmd_print(f"Context %GREEN%'{context or 'ALL'}'%NC% has been reset!")
