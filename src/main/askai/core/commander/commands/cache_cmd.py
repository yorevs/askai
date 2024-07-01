#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.cache_cmd
      @file: cache_cmd.py
   @created: Thu, 27 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, HomeSetup
"""

from abc import ABC
from typing import Optional

from hspylib.core.tools.commons import sysout
from hspylib.core.tools.text_tools import elide_text

from askai.core.component.cache_service import cache
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text


class CacheCmd(ABC):
    """TODO"""

    @staticmethod
    def list() -> None:
        """TODO"""
        if (all_keys := sorted(cache.keys)) and (length := len(all_keys)) > 0:
            display_text(f"### Listing ALL ({length}) Cached Questions:\n\n---\n\n")
            entries: str = ""
            for i, query in enumerate(all_keys, start=1):
                answer: str | None = cache.read_reply(query)
                if not answer:
                    continue
                entries += f"{i}. **{query}**: `{elide_text(answer, 80)}` \n"
            display_text(entries + '\n')
        else:
            sysout(f"\n%RED%-=- Cache is empty! -=-%NC%\n")
        display_text(f"> Hint: Type: '/cache [name | index] to clear one or all cache entries.")

    @staticmethod
    def get(name: str) -> Optional[str]:
        """TODO"""
        return cache.read_reply(name)

    @staticmethod
    def clear(entry: str | int | None = None) -> None:
        """TODO"""
        deleted: str = "No"
        if entry:
            if isinstance(entry, int):
                if name := sorted(cache.keys)[entry]:
                    deleted = cache.del_reply(name)
            elif isinstance(entry, str):
                if name := next((obj for obj in cache.keys if obj == entry), None):
                    deleted = cache.del_reply(name)
        else:
            if deleted := cache.clear_replies():
                deleted = ', '.join(deleted)
        text_formatter.cmd_print(f"'{'%GREEN%' + deleted if deleted else '%YELLOW%No'}'%NC% cache has been cleared!")
