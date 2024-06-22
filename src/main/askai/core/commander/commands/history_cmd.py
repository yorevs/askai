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
import os
import re
from abc import ABC
from textwrap import indent

from hspylib.core.tools.commons import sysout

from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text


class HistoryCmd(ABC):
    """TODO"""

    @staticmethod
    def list() -> None:
        """List the chat context window"""

        # Commander will also change the context itself; so copy it.
        all_context = shared.context
        if (length := len(all_context)) > 0:
            ctx_list = f"### Listing ALL ({length}) Chat Contexts:\n\n---\n\n"
            for c in all_context:
                ctx, ctx_val = c[0], c[1]
                ctx_list += (
                    f"- {ctx} ({len(ctx_val)}/{all_context.max_context_size} "
                    f"tk[{all_context.context_length(ctx)}/{all_context.token_limit}]) \n"
                    + indent(
                        '\n'.join([
                            f'{i}. {e.role.title()}:\n\n{indent(e.content, " " * 4)}'
                            + os.linesep for i, e in enumerate(ctx_val, start=1)
                        ]), ' ' * 4
                    )
                )
            display_text(ctx_list)
            display_text(f"> Hint: Type: '/context forget [context] to forget a it.")
        else:
            sysout(f"\n%YELLOW%-=- Context is empty! -=-%NC%\n")

    @staticmethod
    def forget(context: str | None = None) -> None:
        """Forget entries pushed to the chat context.
        :param context: The context key; or none to forget all context.
        """
        context = context if context != "ALL" else None
        if context:
            shared.context.clear(*(re.split(r"[;,|]", context.upper())))
        else:
            shared.context.forget()
        text_formatter.cmd_print(f"Context %GREEN%'{context.upper() if context else 'ALL'}'%NC% has been cleared!")
