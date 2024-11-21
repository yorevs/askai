#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.history_cmd
      @file: general_cmd.py
   @created: Sat, 22 Jun 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""
from abc import ABC
from typing import Optional

from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from textwrap import indent

import os
import pyperclip
import re


class HistoryCmd(ABC):
    """Provides history command functionalities."""

    @staticmethod
    def context_list() -> None:
        """List the entries in the chat context window."""

        if (all_context := shared.context) and (length := len(all_context)) > 0:
            ln: str = os.linesep
            display_text(f"### Listing ALL ({length}) Chat Contexts:\n\n---\n\n")
            for c in all_context:
                ctx, ctx_val = c[0], c[1]
                display_text(
                    f"- {ctx} ({len(ctx_val)}/{all_context.max_context_size} "
                    f"tk [{all_context.length(ctx)}/{all_context.token_limit}]) \n"
                    + indent(
                        ln.join(
                            [
                                f'{i}. **{e.role.title()}:**\n\n{indent(text_formatter.strip_format(e.content), " " * 4)}'
                                + os.linesep
                                for i, e in enumerate(ctx_val, start=1)
                            ]
                        ),
                        " " * 4,
                    ),
                    markdown=False,
                )
            display_text(f"> Hint: Type: '/context forget [context] to forget a it.")
        else:
            text_formatter.commander_print(f"%YELLOW% Context is empty %NC%")

    @staticmethod
    def context_forget(context: str | None = None) -> None:
        """Forget entries pushed to the chat context.
        :param context: The context key to forget, or None to forget all context entries.
        """
        if context := context if context != "ALL" else None:
            shared.context.clear(*(re.split(r"[;,|]", context.upper())))
        else:
            shared.context.forget()  # Clear the context
            shared.memory.clear()  # Also clear the chat memory
        text_formatter.commander_print(
            f"Context %GREEN%'{context.upper() if context else 'ALL'}'%NC% has been cleared!"
        )

    @staticmethod
    def context_copy(name: str | None = None) -> Optional[str]:
        """Copy a context entry to the clipboard.
        :param name: The name of the context entry to copy. If None, the default context will be copied.
        """
        copied_text: str | None = None
        if (name := name.upper()) in shared.context.keys:
            if (ctx := str(shared.context.flat(name.upper()))) and (
                copied_text := re.sub(
                    r"^((system|human|AI|assistant):\s*)", "", ctx, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE
                )
            ):
                pyperclip.copy(copied_text)
                text_formatter.commander_print(f"`{name}` copied to the clipboard!")
            else:
                text_formatter.commander_print(f"There is nothing to copy from `{name}`!")
        else:
            text_formatter.commander_print(f"Context name not found: `{name}`!")

        return copied_text

    @staticmethod
    def history_list() -> None:
        """List the input history entries."""
        if (history := KeyboardInput.history()) and (length := len(history)):
            history.reverse()
            display_text(f"### Listing ({length}) Input History:\n\n---\n\n")
            padding: int = 1 + len(str(length))
            hist_list: str = ""
            for i, h in enumerate(history, start=1):
                hist_list += f'{f"{i}.":<{padding}} **{h}**\n'
            display_text(hist_list)

    @staticmethod
    def history_forget() -> None:
        """Forget entries pushed to the history."""
        KeyboardInput.forget_history()
