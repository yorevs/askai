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
from askai.core.askai_configs import configs
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text
from functools import partial
from hspylib.core.tools.commons import human_readable_bytes, sysout
from hspylib.core.tools.text_tools import elide_text
from pathlib import Path
from typing import Optional

import os


class CacheCmd(ABC):
    """TODO"""

    @staticmethod
    def list() -> None:
        """TODO"""
        if not configs.is_cache:
            sysout(f"\n%ORANGE%-=- Cache is disabled! -=-%NC%\n")
        elif (all_keys := sorted(cache.keys)) and (length := len(all_keys)) > 0:
            display_text(f"### Listing ALL ({length}) Cached Questions:\n\n---\n\n")
            entries: str = ""
            for i, query in enumerate(all_keys, start=1):
                answer: str | None = cache.read_reply(query)
                if not answer:
                    continue
                entries += f"{i}. **{query}**: `{elide_text(answer, 80)}` \n"
            display_text(entries)
        else:
            sysout(f"\n%RED%-=- Caching is empty! -=-%NC%")
        display_text("\n> Hint: Type: '/cache get/clear [name | index]' to clear one or all cache entries.")

    @staticmethod
    def get(name: str) -> Optional[str]:
        """TODO"""
        entry: str = cache.read_reply(name)
        return (
            f"%GREEN%{name}%NC% cache(s) is %CYAN%\"{entry}\"%NC%"
            if entry else f"%YELLOW%'{name}'%NC% was not found in the cache!"
        )

    @staticmethod
    def clear(entry: str | int | None = None) -> None:
        """TODO"""
        deleted: str | None = None
        if entry:
            if isinstance(entry, int):
                if name := sorted(cache.keys)[entry]:
                    deleted = cache.del_reply(name)
            elif isinstance(entry, str):
                if name := next((obj for obj in cache.keys if obj == entry), None):
                    deleted = cache.del_reply(name)
        else:
            deleted = str(cache.clear_replies())
        text_formatter.cmd_print(
            f"*{deleted if deleted else 'No'}* cache(s) has been cleared!")

    @staticmethod
    def files(cleanup: bool = False, *args: str | int) -> None:
        """TODO"""
        if os.path.exists(CACHE_DIR):
            if cleanup:
                for arg in args[1 if cleanup else 0:]:
                    i_files = Path(f"{CACHE_DIR}").glob(f"{arg}*")
                    while (cached := next(i_files, None)) and os.path.exists(cached):
                        f_join = partial(os.path.join, f"{CACHE_DIR}/{arg}")
                        if os.path.isdir(cached):
                            set(map(os.remove, map(f_join, os.listdir(cached))))
                            text_formatter.cmd_print(f"Folder *{cached}* has been cleared!")
                        elif os.path.isfile(cached):
                            os.remove(cached)
                            text_formatter.cmd_print(f"File **{cached}** was removed!")
            else:
                display_text(f"### Listing cached files from '{CACHE_DIR}':\n\n---\n\n")
                files, dirs = "", ""
                for cached in os.listdir(CACHE_DIR):
                    f_cached = os.path.join(CACHE_DIR, cached)
                    if os.path.isdir(f_cached):
                        f_join = partial(os.path.join, f"{CACHE_DIR}/{cached}")
                        f_all = list(map(os.path.getsize, map(f_join, os.listdir(f_cached))))
                        size, unit = human_readable_bytes(sum(f_all))
                        dirs += f"- *{cached}* ({len(f_all)} files {size} {unit}) \n"
                    else:
                        size, unit = human_readable_bytes(os.path.getsize(f_cached))
                        files += f"- **{cached}** ({size} {unit})\n"
                display_text(f"{dirs}\n{files}")
                display_text(f"\n> Hint: Type: '/cache files cleanup [globs ...]' to delete cached files.")
        else:
            sysout(f"\n%RED%-=- Cache dir {CACHE_DIR} does not exist! -=-%NC%\n")
