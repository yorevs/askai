#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.history_cmd
      @file: general_cmd.py
   @created: Sat, 22 Jun 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from abc import ABC
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from textwrap import indent

import os
import re


class HistoryCmd(ABC):
    """TODO"""

    @staticmethod
    def context_list() -> None:
        """List the chat context window entries."""

        if (all_context := shared.context) and (length := len(all_context)) > 0:
            display_text(f"### Listing ALL ({length}) Chat Contexts:\n\n---\n\n")
            for c in all_context:
                ctx, ctx_val = c[0], c[1]
                display_text(
                    f"- {ctx} ({len(ctx_val)}/{all_context.max_context_size} "
                    f"tk [{all_context.context_length(ctx)}/{all_context.token_limit}]) \n"
                    + indent(
                        '\n'.join([
                            f'{i}. **{e.role.title()}:**\n\n{indent(e.content, " " * 4)}'
                            + os.linesep for i, e in enumerate(ctx_val, start=1)
                        ]), ' ' * 4
                    )
                )
            display_text(f"> Hint: Type: '/context forget [context] to forget a it.")
        else:
            text_formatter.cmd_print(f"%YELLOW% Context is empty %NC%")

    @staticmethod
    def context_forget(context: str | None = None) -> None:
        """Forget entries pushed to the chat context.
        :param context: The context key; or none to forget all context.
        """
        if context := context if context != "ALL" else None:
            shared.context.clear(*(re.split(r"[;,|]", context.upper())))
        else:
            shared.context.forget()
        text_formatter.cmd_print(f"Context %GREEN%'{context.upper() if context else 'ALL'}'%NC% has been cleared!")

    @staticmethod
    def history_list() -> None:
        """List the input history entries."""
        if (history := KeyboardInput.history()) and (length := len(history)):
            history.reverse()
            display_text(f"### Listing ({length}) Input History:\n\n---\n\n")
            padding: int = 1 + len(str(length))
            hist_list: str = ''
            for i, h in enumerate(history, start=1):
                hist_list += f'{f"{i}.":<{padding}} **{h}**\n'
            display_text(hist_list)

    @staticmethod
    def history_forget() -> None:
        """Forget entries pushed to the history."""
        KeyboardInput.forget_history()
